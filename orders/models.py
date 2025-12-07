from django.db import models
from catalog.models import Product, Counterparty, Warehouse
# Product, Counterparty, Warehouse — это наши справочники из приложения catalog


class PurchaseOrder(models.Model):
    """
    Заказ поставщику (твой лист 'Заказ №1').
    В шапке храним общую информацию по заказу.
    """
    number = models.CharField(max_length=50, unique=True)  # номер заказа
    date = models.DateField()                              # дата заказа

    # Фабрика / производство, выбираем только контрагентов типа 'factory'
    factory = models.ForeignKey(
        Counterparty,
        on_delete=models.PROTECT,
        limit_choices_to={'type': 'factory'},
        related_name='purchase_orders',
    )

    currency = models.CharField(
        max_length=3,
        default='RUB',                                     # сом/руб и т.п.
        help_text="Код валюты, например RUB или KGS",
    )

    status = models.CharField(
        max_length=20,
        default='draft',
        help_text="Статус заказa: draft / in_progress / closed",
    )

    # Общая сумма заказа (можно не заполнять руками, а считать по строкам)
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
        ordering = ['-date']  # в списках сначала свежие заказы


class ProductBatch(models.Model):
    """
    Партия товара внутри заказа: артикул + цвет + размер.
    Это соответствует строкам 'блузка ... S/M/L' в таблице.
    """
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
