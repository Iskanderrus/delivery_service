from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("orders/", include("apps.orders.urls")),
    path("products/", include("apps.products.urls")),
]
