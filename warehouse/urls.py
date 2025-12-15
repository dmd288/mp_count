from django.urls import path
from .views import stock_balance_view

app_name = "warehouse"

urlpatterns = [
    path("stock-balance/", stock_balance_view, name="stock_balance"),
]
