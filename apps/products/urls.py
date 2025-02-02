from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CreateCategoryView, CreateProductView, ProductListView

app_name = "products"

urlpatterns = [
    path("create-product/", CreateProductView.as_view(), name="create-product"),
    path("create-category/", CreateCategoryView.as_view(), name="create-category"),
]
