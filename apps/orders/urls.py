from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import create_order_from_product, order_list

app_name = "orders"

urlpatterns = [
    path("orders-all/", order_list, name="order-list"),
    path(
        "orders/create/<int:product_id>/",
        create_order_from_product,
        name="create-order-from-product",
    ),
]
