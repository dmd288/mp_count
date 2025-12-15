from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce

from catalog.models import Warehouse
from orders.models import ProductBatch
from .models import (
    TechCard,
    ConsumablePurchaseItem,
    ConsumableStockMovement,
    ConsumableStockMovementItem,
)


def get_consumable_balance(warehouse: Warehouse):
    """
    Остатки расходников на складе: dict {consumable_id: qty}
    """

    qs = ConsumableStockMovementItem.objects.filter(
        Q(movement__warehouse_to=warehouse) | Q(movement__warehouse_from=warehouse)
    ).select_related("movement")

    incoming = (
        qs.filter(movement__warehouse_to=warehouse)
        .values("consumable_id")
        .annotate(qty=Coalesce(Sum("quantity"), 0))
    )
    outgoing = (
        qs.filter(movement__warehouse_from=warehouse)
        .values("consumable_id")
        .annotate(qty=Coalesce(Sum("quantity"), 0))
    )

    in_map = {r["consumable_id"]: r["qty"] for r in incoming}
    out_map = {r["consumable_id"]: r["qty"] for r in outgoing}

    all_ids = set(in_map) | set(out_map)
    return {cid: in_map.get(cid, 0) - out_map.get(cid, 0) for cid in all_ids}


def _last_purchase_price_rub(consumable_id: int) -> Decimal:
    last = (
        ConsumablePurchaseItem.objects.filter(consumable_id=consumable_id)
        .select_related("purchase")
        .order_by("-purchase__date", "-id")
        .first()
    )
    if not last:
        raise ValidationError(f"Нет закупочной цены для расходника id={consumable_id}")
    return last.unit_price_rub


def _get_techcard_for_batch(batch: ProductBatch) -> TechCard:
    """
    1) Если у партии задан batch.tech_card — используем его
    2) Иначе берём дефолтную техкарту товара (TechCard.product = batch.product, is_default=True)
    """
    if hasattr(batch, "tech_card_id") and batch.tech_card_id:
        return batch.tech_card

    tc = (
        TechCard.objects
        .filter(product=batch.product, is_default=True)
        .order_by("-id")
        .first()
    )
    if not tc:
        raise ValidationError(
            f"Нет дефолтной техкарты для товара {batch.product.article}. "
            f"Создай TechCard и поставь is_default=True."
        )
    return tc

@transaction.atomic
def writeoff_by_techcard(batch: ProductBatch, materials_warehouse: Warehouse):
    """
    Списывает расходники по техкарте партии и записывает себестоимость материалов в партию.
    """
    techcard = _get_techcard_for_batch(batch)

    if not batch.quantity_planned or batch.quantity_planned <= 0:
        raise ValidationError("quantity_planned у партии должен быть > 0")

    # потребность
    need = {}
    for item in techcard.items.select_related("consumable").all():
        qty = (item.quantity_per_unit * Decimal(batch.quantity_planned))
        need[item.consumable_id] = need.get(item.consumable_id, Decimal("0")) + qty

    # остатки
    balance = get_consumable_balance(materials_warehouse)

    shortages = []
    for cid, req in need.items():
        have = balance.get(cid, Decimal("0"))
        if have < req:
            shortages.append((cid, req, have))

    if shortages:
        msg = "Не хватает расходников:\n" + "\n".join(
            [f"- id={cid}: нужно {req}, есть {have}" for cid, req, have in shortages]
        )
        raise ValidationError(msg)

    # создаём документ списания
    move = ConsumableStockMovement.objects.create(
        doc_type="writeoff",
        warehouse_from=materials_warehouse,
        warehouse_to=None,
        related_purchase=None,
        comment=f"Списание по техкарте партии {batch.id}",
    )

    total_cost = Decimal("0.00")

    for cid, req in need.items():
        price = _last_purchase_price_rub(cid)
        ConsumableStockMovementItem.objects.create(
            movement=move,
            consumable_id=cid,
            quantity=req,
            unit_cost_rub=price,
        )
        total_cost += (req * price)

    batch.material_cost_total = total_cost
    batch.material_cost_per_unit = (total_cost / Decimal(batch.quantity_planned))
    batch.save(update_fields=["material_cost_total", "material_cost_per_unit"])

    return move