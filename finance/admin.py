from django.contrib import admin
from .models import MoneyAccount, ExpenseIncomeCategory, MoneyTransaction


@admin.register(MoneyAccount)
class MoneyAccountAdmin(admin.ModelAdmin):
    """
    Настройки отображения счетов в админке.
    """
    list_display = ("name", "currency")
    list_filter = ("currency",)
    search_fields = ("name",)


@admin.register(ExpenseIncomeCategory)
class ExpenseIncomeCategoryAdmin(admin.ModelAdmin):
    """
    Справочник статей движения денег.
    """
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(MoneyTransaction)
class MoneyTransactionAdmin(admin.ModelAdmin):
    """
    Список всех денежных операций:
    - удобные фильтры по типу, заказу, контрагенту, статье,
    - быстрый поиск по комментариям.
    """
    list_display = (
        "date", "tran_type", "amount", "currency",
        "account_from", "account_to",
        "order", "counterparty", "category",
    )
    list_filter = ("tran_type", "currency", "account_from", "account_to", "category")
    date_hierarchy = "date"
    search_fields = ("comment", "order__number", "counterparty__name")
