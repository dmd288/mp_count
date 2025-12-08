from django.db import models
from catalog.models import Warehouse
from orders.models import ProductBatch, Supply


class StockMovement(models.Model):
    """
    Документ складского движения.
    Через него фиксируем:
    - приход товара (например, из поставки по заказу),
    - расход (отгрузка, продажа),
    - перемещение между складами,
    - списание (брак, утилизация),
    - инвентаризацию.
    На основе всех таких документов будем считать остатки.
    """
    MOVEMENT_TYPES = [
        ('income', 'Приход'),
        ('outcome', 'Расход'),
        ('transfer', 'Перемещение'),
        ('writeoff', 'Списание'),
        ('inventory', 'Инвентаризация'),
    ]

    doc_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        help_text="Тип движения: приход/расход/перемещение/списание/инвентаризация",
    )

    date = models.DateTimeField(
        auto_now_add=True,
        help_text="Когда было зафиксировано движение",
    )

    # Откуда и куда едет товар:
    # - для прихода usually warehouse_to не пустой, warehouse_from = NULL,
    # - для расхода наоборот,
    # - для перемещения оба склада заполнены,
    # - для списания только warehouse_from.
    warehouse_from = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='outgoing_movements',
        help_text="Склад-источник (может быть пустым для прихода)",
    )

    warehouse_to = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='incoming_movements',
        help_text="Склад-получатель (может быть пустым для расхода)",
    )

    # Связь с Supply: приход по поставке по заказу.
    related_supply = models.ForeignKey(
        Supply,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        help_text="Если движение связано с конкретной поставкой",
    )

    comment = models.CharField(
        max_length=255,
        blank=True,
        help_text="Произвольный комментарий к документу движения",
    )

    def __str__(self):
        return f"{self.get_doc_type_display()} от {self.date:%Y-%m-%d %H:%M}"


class StockMovementItem(models.Model):
    """
    Строка складского движения.
    Здесь храним, какие партии и в каком количестве поехали в рамках документа.
    Именно по этим строкам будет считаться остаток по каждой партии и складу.
    """
    movement = models.ForeignKey(
        StockMovement,
        on_delete=models.CASCADE,
        related_name='items',
    )

    batch = models.ForeignKey(
        ProductBatch,
        on_delete=models.PROTECT,
        related_name='stock_items',
        help_text="Партия товара, к которой относится движение",
    )

    quantity = models.PositiveIntegerField(
        help_text="Количество единиц в этом движении",
    )

    def __str__(self):
        return f"{self.movement} | {self.batch} x {self.quantity}"
