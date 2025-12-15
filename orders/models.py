from django.db import models
from catalog.models import Product, Counterparty, Warehouse
from decimal import Decimal
# Product, Counterparty, Warehouse — это наши справочники из приложения catalog


class PurchaseOrder(models.Model):
    """
    Заказ поставщику (твой лист 'Заказ №1').
    """
    number = models.CharField(max_length=50, unique=True)
    date = models.DateField()

    factory = models.ForeignKey(
        Counterparty,
        on_delete=models.PROTECT,
        limit_choices_to={'type': 'factory'},
        related_name='purchase_orders',
    )

    currency = models.CharField(
        max_length=3,
        default='RUB',
        help_text="Код валюты, например RUB или KGS",
    )

    status = models.CharField(
        max_length=20,
        default='draft',
        help_text="Статус заказa: draft / in_progress / closed",
    )

    total_amount_currency = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Сумма заказа в валюте (из строк заказа)",
    )
    total_amount_rub = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Сумма заказа в рублях",
    )

    def __str__(self):
        return f"Заказ {self.number} от {self.date}"

    class Meta:
        ordering = ['-date']

    # ==== Финансовые агрегаты по заказу ====

    def get_paid_amount_currency(self):
        """
        Сколько всего оплачено по заказу в валюте заказа.
        """
        from finance.models import MoneyTransaction  # локальный импорт, чтобы избежать циклов

        qs = MoneyTransaction.objects.filter(
            order=self,
            tran_type='expense',
            currency=self.currency,
        )
        total = qs.aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total

    def get_paid_amount_rub(self):
        """
        Оплачено в рублях (с учётом курса).
        """
        from finance.models import MoneyTransaction

        qs = MoneyTransaction.objects.filter(
            order=self,
            tran_type='expense',
        )
        total = 0
        for tx in qs:
            if tx.currency == 'RUB':
                total += tx.amount
            else:
                total += tx.amount * tx.exchange_rate
        return total

    def get_outstanding_amount_currency(self):
        """
        Осталось оплатить в валюте заказа.
        """
        return (self.total_amount_currency or 0) - (self.get_paid_amount_currency() or 0)

    def get_outstanding_amount_rub(self):
        """
        Осталось оплатить в рублях.
        """
        return (self.total_amount_rub or 0) - (self.get_paid_amount_rub() or 0)



class ProductBatch(models.Model):
    """
    Партия товара внутри заказа: артикул + цвет + размер.
    Это соответствует строкам 'блузка ... S/M/L' в таблице.
    """

    material_cost_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    material_cost_per_unit = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0.0000"))

    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='batches',          # order.batches.all()
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='batches',          # product.batches.all()
    )
    color = models.CharField(max_length=50, blank=True)  # цвет (если нужен отдельно)
    size = models.CharField(max_length=20, blank=True)   # размер
    quantity_planned = models.PositiveIntegerField()     # всего по заказу (ИТОГО в строке)

    # позже сюда можно добавить статусы партии (в пути, в ФФ, на WB и т.д.)

    def __str__(self):
        return f"{self.order.number} | {self.product.article} {self.size} ({self.quantity_planned})"


class PurchaseOrderItem(models.Model):
    """
    Строка заказа поставщику.
    Можно дублировать данные из ProductBatch или делить партию на подстроки.
    """
    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',            # order.items.all()
    )
    batch = models.ForeignKey(
        ProductBatch,
        on_delete=models.PROTECT,
        related_name='order_items',      # batch.order_items.all()
    )
    quantity = models.PositiveIntegerField()  # количество в этой строке
    price_currency = models.DecimalField(
        max_digits=12, decimal_places=2
    )                                        # цена за 1 единицу в валюте
    amount_currency = models.DecimalField(
        max_digits=12, decimal_places=2
    )                                        # сумма в валюте = quantity * price_currency

    def __str__(self):
        return f"{self.order.number} | {self.batch} x {self.quantity}"


class Supply(models.Model):
    """
    Поставка по заказу (Поставка №1, №2 ...).
    Это твой блок 'Поставка №1..№N' в заказе.
    """
    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='supplies',          # order.supplies.all()
    )
    number = models.CharField(max_length=50)   # номер поставки (можно WB‑номер)
    date = models.DateField()                 # дата поставки
    status = models.CharField(
        max_length=20,
        default='in_transit',
        help_text="in_transit / arrived / accepted",
    )

    def __str__(self):
        return f"Поставка {self.number} по заказу {self.order.number}"


class SupplyItem(models.Model):
    """
    Строка поставки: сколько штук какой партии приехало на какой склад.
    Это распределение по складам 'Электросталь / Екатеринбург / ...'.
    """
    supply = models.ForeignKey(
        Supply,
        on_delete=models.CASCADE,
        related_name='items',             # supply.items.all()
    )
    batch = models.ForeignKey(
        ProductBatch,
        on_delete=models.PROTECT,
        related_name='supply_items',      # batch.supply_items.all()
    )
    warehouse_to = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='incoming_supply_items',
    )
    quantity = models.PositiveIntegerField()   # сколько единиц отправили на этот склад

    def __str__(self):
        return f"{self.supply} -> {self.warehouse_to} ({self.quantity})"




    # ==== Финансовые агрегаты по заказу ====

    def get_paid_amount_currency(self):
        """
        Сколько всего оплачено по заказу в валюте операции.
        Берём все денежные операции, привязанные к этому заказу,
        где тип = 'expense' (расход, то есть мы платим поставщику)
        и валюта совпадает с валютой заказа.
        """
        from finance.models import MoneyTransaction  # локальный импорт, чтобы избежать циклов

        qs = MoneyTransaction.objects.filter(
            order=self,
            tran_type='expense',
            currency=self.currency,
        )
        total = qs.aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total

    def get_paid_amount_rub(self):
        """
        Оплачено в рублях (с учётом курса).
        Берём все операции по заказу типа 'expense' и пересчитываем в RUB.
        """
        from finance.models import MoneyTransaction

        qs = MoneyTransaction.objects.filter(
            order=self,
            tran_type='expense',
        )
        # amount * exchange_rate (если валютная операция)
        total = 0
        for tx in qs:
            if tx.currency == 'RUB':
                total += tx.amount
            else:
                total += tx.amount * tx.exchange_rate
        return total

    def get_outstanding_amount_currency(self):
        """
        Осталось оплатить в валюте заказа:
        сумма заказа в валюте - оплачено в валюте.
        """
        return (self.total_amount_currency or 0) - (self.get_paid_amount_currency() or 0)

    def get_outstanding_amount_rub(self):
        """
        Осталось оплатить в рублях:
        сумма заказа в рублях - оплачено в рублях.
        """
        return (self.total_amount_rub or 0) - (self.get_paid_amount_rub() or 0)

