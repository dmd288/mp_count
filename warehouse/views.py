from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.db import models

from catalog.models import Warehouse
from .models import StockMovementItem


def stock_balance_view(request):
    article = request.GET.get("article")
    warehouse_id = request.GET.get("warehouse")

    base = StockMovementItem.objects.select_related(
        "movement",
        "batch",
        "batch__product",
        "movement__warehouse_from",
        "movement__warehouse_to",
    )

    if article:
        base = base.filter(batch__product__article__icontains=article)

    # ---------- INCOME (warehouse_to) ----------
    income_qs = base.filter(movement__doc_type="income")
    if warehouse_id:
        income_qs = income_qs.filter(movement__warehouse_to_id=warehouse_id)

    income = (
        income_qs.values(
            "batch_id",
            "movement__warehouse_to_id",
            "batch__product__article",
            "batch__product__name",
            "batch__size",
            "batch__color",
            "movement__warehouse_to__name",
        )
        .annotate(income_qty=Coalesce(Sum("quantity"), 0))
    )

    # ---------- OUTCOME (warehouse_from): outcome + transfer + writeoff ----------
    outcome_qs = base.filter(movement__doc_type__in=["outcome", "transfer", "writeoff"])
    if warehouse_id:
        outcome_qs = outcome_qs.filter(movement__warehouse_from_id=warehouse_id)

    outcome = (
        outcome_qs.values(
            "batch_id",
            "movement__warehouse_from_id",
        )
        .annotate(outcome_qty=Coalesce(Sum("quantity"), 0))
    )

    # индексируем расход по ключу (batch_id, warehouse_id)
    outcome_map = {
        (r["batch_id"], r["movement__warehouse_from_id"]): r["outcome_qty"] for r in outcome
    }

    rows = []
    for r in income:
        key = (r["batch_id"], r["movement__warehouse_to_id"])
        bal = r["income_qty"] - outcome_map.get(key, 0)
        if bal <= 0:
            continue

        rows.append(
            {
                "batch_id": r["batch_id"],
                "article": r["batch__product__article"],
                "name": r["batch__product__name"],
                "size": r["batch__size"],
                "color": r["batch__color"],
                "warehouse_name": r["movement__warehouse_to__name"] or "—",
                "balance": bal,
            }
        )

    warehouses = Warehouse.objects.all()
    context = {
        "rows": rows,
        "warehouses": warehouses,
        "selected_warehouse": int(warehouse_id) if warehouse_id else None,
        "article": article or "",
    }
    return render(request, "warehouse/stock_balance.html", context)