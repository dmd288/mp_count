from django.contrib import admin
from .models import PurchaseOrder, ProductBatch, PurchaseOrderItem, Supply, SupplyItem


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """
    Настройки отображения заказов в админке.
    Здесь сразу показываем:
    - общие суммы,
    - сколько оплачено,
    - сколько осталось оплатить.
    """
    list_display = (
        "number", "date", "factory", "currency", "status",
        "total_amount_currency", "total_amount_rub",
        "paid_amount_currency", "paid_amount_rub",
        "outstanding_amount_currency", "outstanding_amount_rub",
    )
    list_filter = ("status", "currency", "factory")
    search_fields = ("number",)
    date_hierarchy = "date"

    # Эти методы берут значения из методов модели PurchaseOrder
    def paid_amount_currency(self, obj):
        return obj.get_paid_amount_currency()
    paid_amount_currency.short_description = "Оплачено (валюта)"

    def paid_amount_rub(self, obj):
        return obj.get_paid_amount_rub()
    paid_amount_rub.short_description = "Оплачено (руб)"

    def outstanding_amount_currency(self, obj):
        return obj.get_outstanding_amount_currency()
    outstanding_amount_currency.short_description = "Остаток (валюта)"

    def outstanding_amount_rub(self, obj):
        return obj.get_outstanding_amount_rub()
    outstanding_amount_rub.short_description = "Остаток (руб)"



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
