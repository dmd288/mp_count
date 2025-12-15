from django.contrib import admin
from .models import (
    ConsumablePurchase,
    ConsumablePurchaseItem,
    TechCard,
    TechCardItem,
)


class ConsumablePurchaseItemInline(admin.TabularInline):
    """
    Встроенные строки закупки расходников в форме документа.
    Позволяет в админке сразу добавлять позиции закупки.
    """
    model = ConsumablePurchaseItem
    extra = 1


@admin.register(ConsumablePurchase)
class ConsumablePurchaseAdmin(admin.ModelAdmin):
    """
    Список закупок расходников:
    кто, когда и в какой валюте продавал.
    """
    list_display = ("date", "supplier", "currency")
    list_filter = ("supplier", "currency", "date")
    date_hierarchy = "date"
    inlines = [ConsumablePurchaseItemInline]


@admin.register(ConsumablePurchaseItem)
class ConsumablePurchaseItemAdmin(admin.ModelAdmin):
    """
    Отдельный просмотр строк закупки (обычно не нужен,
    но полезен для поиска по расходнику).
    """
    list_display = ("purchase", "consumable", "quantity", "amount_rub", "unit_price_rub")
    list_filter = ("consumable", "purchase__supplier")
    search_fields = ("consumable__name",)


class TechCardItemInline(admin.TabularInline):
    """
    Строки техкарты в форме техкарты.
    """
    model = TechCardItem
    extra = 1


@admin.register(TechCard)
class TechCardAdmin(admin.ModelAdmin):
    """
    Техкарта: к какому товару относится и как называется.
    """
    list_display = ("product", "name", "is_default")
    list_filter = ("is_default",)
    search_fields = ("name", "product__article", "product__name")
    inlines = [TechCardItemInline]


@admin.register(TechCardItem)
class TechCardItemAdmin(admin.ModelAdmin):
    """
    Отдельный просмотр строк техкарты.
    """
    list_display = ("techcard", "consumable", "quantity_per_unit")
    list_filter = ("consumable",)
    search_fields = ("techcard__name", "consumable__name")
