from django.contrib import admin
from .models import Product, Warehouse, Counterparty, Consumable

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("article", "name", "size", "color", "category")
    search_fields = ("article", "name")
    list_filter = ("category", "size", "color")

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type",)

@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "phone", "email")
    list_filter = ("type",)
    search_fields = ("name",)

@admin.register(Consumable)
class ConsumableAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "color")
    search_fields = ("name",)
