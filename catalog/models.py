from django.db import models

class Product(models.Model):
    # Карточка товара / артикула
    article = models.CharField(max_length=50, unique=True)  # артикул
    name = models.CharField(max_length=200)                 # наименование
    color = models.CharField(max_length=50, blank=True)     # цвет
    size = models.CharField(max_length=20, blank=True)      # размер
    category = models.CharField(max_length=100, blank=True) # категория (платье, блузка и т.п.)

    def __str__(self):
        return f"{self.article} {self.name} {self.size} {self.color}"

class Warehouse(models.Model):
    # Тип склада/локации
    WAREHOUSE_TYPES = [
        ('production', 'Производство'),        # цех, фабрика, пошив
        ('ff', 'Фулфилмент'),                 # любой ФФ (Бишкек, Москва и т.д.)
        ('cargo', 'Карго / Транзит'),         # склады карго, хабы
        ('mp_warehouse', 'Склад маркетплейса'),  # склады WB/Ozon/YM
        ('own', 'Собственный склад'),         # свои склады (если появятся)
        ('other', 'Другое'),
    ]
    name = models.CharField(max_length=200)   # конкретное название: "ФФ Бишкек", "Карго Рад Экспресс"
    type = models.CharField(max_length=20, choices=WAREHOUSE_TYPES, default='other')

    def __str__(self):
        return self.name

class Counterparty(models.Model):
    # Поставщики, карго, фулфилменты, транспортные и т.п.
    COUNTERPARTY_TYPES = [
        ('factory', 'Фабрика'),
        ('cargo', 'Карго-компания'),
        ('ff', 'Фулфилмент'),
        ('carrier', 'Транспортная компания'),
        ('wb', 'Wildberries'),
        ('other', 'Другое'),
    ]
    name = models.CharField(max_length=200)                 # название контрагента
    type = models.CharField(max_length=20, choices=COUNTERPARTY_TYPES, default='other')
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

class Consumable(models.Model):
    # Расходники: ткань, бирки, упаковка и т.п.
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=20)                  # м, шт, кг и т.п.

    def __str__(self):
        return self.name
