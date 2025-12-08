from django.contrib import admin
from .models import StockMovement, StockMovementItem


class StockMovementItemInline(admin.TabularInline):
    """
    Встроенные строки движения товара в форме документа.
    Позволяет в админке сразу добавлять позиции (партии и количества).
    """
    model = StockMovementItem
    extra = 0   # не показывать лишние пустые строки по умолчанию


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """
    Отображение документов движения в админке:
    - список документов,
    - фильтры по типам, складам и датам.
    """
    list_display = ("doc_type", "date", "warehouse_from", "warehouse_to", "related_supply")
    list_filter = ("doc_type", "warehouse_from", "warehouse_to", "date")
    date_hierarchy = "date"
    inlines = [StockMovementItemInline]


@admin.register(StockMovementItem)
class StockMovementItemAdmin(admin.ModelAdmin):
    """
    Отдельное отображение строк движения (редко нужно,
    но может быть полезно для поиска по партии).
    """
    list_display = ("movement", "batch", "quantity")
    list_filter = ("batch",)
    search_fields = ("movement__id", "batch__product__article", "batch__product__name")
