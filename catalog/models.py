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
    # Склады: производство, карго, ФФ Бишкек, ФФ Москва, WB и т.д.
    WAREHOUSE_TYPES = [
        ('production', 'Производство'),
        ('cargo', 'Карго'),
        ('ff_bishkek', 'Фулфилмент Бишкек'),
        ('ff_moscow', 'Фулфилмент Москва'),
        ('wb', 'Склад WB'),
        ('other', 'Другой'),
    ]
    name = models.CharField(max_length=200)                 # название склада
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
