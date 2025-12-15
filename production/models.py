from django.db import models

from catalog.models import Consumable, Counterparty, Warehouse, Product

# Consumable  – справочник расходников (ткань, бирки, упаковка и т.п.)
# Counterparty – контрагенты (в т.ч. поставщики расходников)
# Warehouse   – склады (в том числе склады производителей)
# ProductBatch – партии готовых изделий


# ==========================
#  Закупка расходников
# ==========================

class ConsumablePurchase(models.Model):
    """
    Документ закупки расходников.
    Аналог листа 'Поставщик' для расходников:
    - кто продал,
    - когда,
    - в какой валюте.
    Факта движения по складам ещё нет, только покупка.
    """
    supplier = models.ForeignKey(
        Counterparty,
        on_delete=models.PROTECT,
        # при желании можно ослабить фильтр (оставить всех контрагентов)
        related_name='consumable_purchases',
        help_text="Поставщик расходников",
    )
    date = models.DateField(help_text="Дата закупки расходников")
    currency = models.CharField(
        max_length=3,
        default='RUB',
        help_text="Валюта закупки: RUB, KGS и т.п.",
    )

    def __str__(self):
        return f"Закупка расходников от {self.date} ({self.supplier})"


class ConsumablePurchaseItem(models.Model):
    """
    Строка закупки расходников:
    - какой расходник,
    - сколько купили,
    - по какой цене.
    Здесь храним уже готовую цену за единицу в рублях,
    чтобы не зависеть от формул в таблицах и не ловить #DIV/0!.
    """
    purchase = models.ForeignKey(
        ConsumablePurchase,
        on_delete=models.CASCADE,
        related_name='items',
    )
    consumable = models.ForeignKey(
        Consumable,
        on_delete=models.PROTECT,
        related_name='purchase_items',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Количество (м/шт/кг) по документу",
    )
    amount_rub = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Сумма в рублях (полная сумма строки)",
    )
    unit_price_rub = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Цена за 1 единицу в рублях",
    )

    def __str__(self):
        return f"{self.consumable} x {self.quantity} (покупка {self.purchase_id})"


# ==========================
#  Движение расходников по складам
# ==========================

class ConsumableStockMovement(models.Model):
    """
    Документ движения расходников между складами:
    - income   – приход после закупки,
    - transfer – перемещение между складами/производствами,
    - writeoff – списание на производство (по техкарте).
    По этим документам будет считаться остаток расходников по складам.
    """
    MOVEMENT_TYPES = [
        ('income', 'Приход'),
        ('transfer', 'Перемещение'),
        ('writeoff', 'Списание'),
    ]

    doc_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        help_text="Тип движения расходников",
    )
    date = models.DateTimeField(
        auto_now_add=True,
        help_text="Когда зафиксировано движение",
    )

    # Откуда и куда двигаются расходники:
    # - income: warehouse_to заполнен, warehouse_from = NULL;
    # - transfer: оба склада заполнены;
    # - writeoff: warehouse_from заполнен, warehouse_to = NULL.
    warehouse_from = models.ForeignKey(
        Warehouse,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='consumable_out_movements',
        help_text="Склад-источник (для списаний/перемещений)",
    )
    warehouse_to = models.ForeignKey(
        Warehouse,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='consumable_in_movements',
        help_text="Склад-получатель (для приходов/перемещений)",
    )

    # Для прихода можно связать движение с документом закупки
    related_purchase = models.ForeignKey(
        ConsumablePurchase,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stock_movements',
        help_text="Закупка, из которой пришли расходники (для прихода)",
    )

    comment = models.CharField(
        max_length=255,
        blank=True,
        help_text="Комментарий к движению (номер накладной, причина и т.п.)",
    )

    def __str__(self):
        return f"{self.get_doc_type_display()} расходников от {self.date:%Y-%m-%d %H:%M}"


class ConsumableStockMovementItem(models.Model):
    """
    Строка движения расходников:
    - какой расходник,
    - сколько списали/переместили/приняли,
    - по какой учётной цене.
    """
    movement = models.ForeignKey(
        ConsumableStockMovement,
        on_delete=models.CASCADE,
        related_name='items',
    )
    consumable = models.ForeignKey(
        Consumable,
        on_delete=models.PROTECT,
        related_name='stock_items',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Количество расходника в этом движении",
    )
    unit_cost_rub = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Учётная цена за единицу на момент движения",
    )

    def __str__(self):
        return f"{self.movement} | {self.consumable} x {self.quantity}"


# ==========================
#  Техкарты
# ==========================
from django.db import models
from django.db.models import Q


class TechCard(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tech_cards",
        help_text="Товар, для которого действует техкарта",
    )
    name = models.CharField(max_length=200)
    is_default = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_default=True),
                name="uniq_default_techcard_per_product",
            )
        ]

    def __str__(self):
        return f"Техкарта {self.name} для {self.product.article}"
    

class TechCardItem(models.Model):
    techcard = models.ForeignKey(TechCard, on_delete=models.CASCADE, related_name="items")
    consumable = models.ForeignKey(Consumable, on_delete=models.PROTECT, related_name="techcard_items")
    quantity_per_unit = models.DecimalField(max_digits=12, decimal_places=3)

    def __str__(self):
        return f"{self.techcard} | {self.consumable} x {self.quantity_per_unit} на 1 шт."
