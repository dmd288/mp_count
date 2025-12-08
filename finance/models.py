from django.db import models
from orders.models import PurchaseOrder
from catalog.models import Counterparty


class MoneyAccount(models.Model):
    """
    Денежный счёт.
    Это может быть:
    - расчётный счёт в банке,
    - касса (наличные),
    - счёт в другой валюте.
    Из этих счетов будут списываться и на них приходить деньги.
    """
    name = models.CharField(max_length=100)           # Название счёта (например, "Р/с Tinkoff", "Касса")
    currency = models.CharField(max_length=3, default='RUB')  # Валюта счёта: RUB, KGS и т.п.

    def __str__(self):
        return f"{self.name} ({self.currency})"


class ExpenseIncomeCategory(models.Model):
    """
    Статья движения денег.
    Нужно для аналитики: понимать, куда уходят/откуда приходят деньги.
    Примеры:
    - "Оплата поставщику",
    - "Карго",
    - "Фулфилмент Москва",
    - "Возврат от WB" и т.д.
    """
    name = models.CharField(max_length=100)           # Название статьи

    def __str__(self):
        return self.name


class MoneyTransaction(models.Model):
    """
    Денежная операция.
    Универсальная модель, которая покрывает:
    - приход денег (income),
    - расход денег (expense),
    - перемещение между счетами (transfer).

    Каждая операция может быть привязана:
    - к заказу поставщику (PurchaseOrder),
    - к контрагенту (Counterparty),
    - к статье (ExpenseIncomeCategory).
    Это очень похоже на то, как это сделано в МойСклад.
    """
    TRANSACTION_TYPES = [
        ('income', 'Приход'),
        ('expense', 'Расход'),
        ('transfer', 'Перемещение'),
    ]

    tran_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        help_text="Тип операции: приход / расход / перемещение",
    )

    date = models.DateField(
        help_text="Дата операции (когда реально прошёл платёж)",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Сумма операции в валюте операции",
    )

    currency = models.CharField(
        max_length=3,
        default='RUB',
        help_text="Валюта операции: RUB, KGS и т.п.",
    )

    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1,
        help_text="Курс к рублю, если операция не в рублях (для пересчёта в отчёты)",
    )

    # С каких и на какие счета идут деньги.
    # Для прихода:
    #   account_to заполнен, account_from = NULL.
    # Для расхода:
    #   account_from заполнен, account_to = NULL.
    # Для перемещения:
    #   заполнены оба.
    account_from = models.ForeignKey(
        MoneyAccount,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='outgoing_transactions',
        help_text="Счёт, с которого списываются деньги (для расхода/перемещения)",
    )

    account_to = models.ForeignKey(
        MoneyAccount,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='incoming_transactions',
        help_text="Счёт, на который приходят деньги (для прихода/перемещения)",
    )

    # Связь с бизнес-сущностями:
    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='money_transactions',
        help_text="Заказ поставщику, к которому относится платёж (если есть)",
    )

    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='money_transactions',
        help_text="Контрагент (фабрика, карго, фулфилмент, WB), к которому относится операция",
    )

    category = models.ForeignKey(
        ExpenseIncomeCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='money_transactions',
        help_text="Статья движения денег (для аналитики)",
    )

    comment = models.CharField(
        max_length=255,
        blank=True,
        help_text="Любой комментарий: номер счёта, платёжки и т.п.",
    )

    def __str__(self):
        return f"{self.get_tran_type_display()} {self.amount} {self.currency} от {self.date}"
