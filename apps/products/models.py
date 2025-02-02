from django.db import models

from apps.accounts.models import CustomUser


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": "shop"}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name
