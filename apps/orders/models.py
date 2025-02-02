from django.db import models
from apps.accounts.models import CustomUser
from apps.products.models import Product
from django.utils.translation import gettext_lazy as _


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product, related_name="orderitems", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey("Order", related_name="items", on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.product.price
        super().save(*args, **kwargs)


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ("created", _("Order created")),
        ("submitted", _("Order submitted")),
        ("pending", _("Order pending")),
        ("assigned", _("Order assigned")),
        ("in_transit", _("Order in transit")),
        ("delivered", _("Order delivered")),
    ]
    total_amount = models.DecimalField(
        _("Total amount"), max_digits=10, decimal_places=10, default=0
    )
    delivery_price = models.DecimalField(
        _("Delivery price"), max_digits=10, decimal_places=10, default=0
    )
    shop = models.ForeignKey(
        CustomUser,
        related_name="shop_orders",
        on_delete=models.CASCADE,
        limit_choices_to={"role": "shop"},
        verbose_name="Shop",
    )
    driver = models.ForeignKey(
        CustomUser,
        related_name="driver_orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": "driver"},
        verbose_name="Driver",
    )
    customer = models.ForeignKey(
        CustomUser,
        related_name="customer_orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": "customer"},
        verbose_name="Customer",
    )
    pickup_address = models.CharField(
        max_length=255, verbose_name="Pick-Up Address", null=True, blank=True
    )
    dropoff_address = models.CharField(
        max_length=255, verbose_name="Drop-Off Address", null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="created",
        verbose_name=_("Order status"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"
