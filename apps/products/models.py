from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q

from apps.accounts.models import CustomUser


class Category(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    class Meta:
        constraints = (
            CheckConstraint(
                check=Q(weight__gte=0.0) & Q(weight__lte=1.0),
                name="weight_range",
            ),
        )

    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    supplier = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": "shop"}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.category})"
