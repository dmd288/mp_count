from django.contrib import admin
from .models import PurchaseOrder, ProductBatch, PurchaseOrderItem, Supply, SupplyItem


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """
    Настройки отображения заказов в админке:
    какие колонки видеть, по каким полям фильтровать.
    """
    list_display = (
        "number", "date", "factory", "currency", "status",
        "total_amount_currency", "total_amount_rub",
    )
    list_filter = ("status", "currency", "factory")
    search_fields = ("number",)
    date_hierarchy = "date"


@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "color", "size", "quantity_planned")
    list_filter = ("order", "product", "size", "color")
    search_fields = ("product__article", "product__name")


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "batch", "quantity", "price_currency", "amount_currency")
    list_filter = ("order",)
    search_fields = ("order__number", "batch__product__article")


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ("number", "order", "date", "status")
    list_filter = ("status", "date", "order")
    search_fields = ("number", "order__number")


@admin.register(SupplyItem)
class SupplyItemAdmin(admin.ModelAdmin):
    list_display = ("supply", "batch", "warehouse_to", "quantity")
    list_filter = ("warehouse_to", "supply__order")
    search_fields = ("supply__number", "batch__product__article")
