from django.db import models
from apps.accounts.models import CustomUser


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DF", "Черновик"
        PUBLISHED = "PB", "Опубликован"
        ARCHIVED = "AR", "Архивирован"

    shop = models.ForeignKey(
        CustomUser, related_name='shops', on_delete=models.CASCADE, limit_choices_to={'role': 'shop'}, verbose_name='Shop')
    driver = models.ForeignKey(CustomUser, related_name='drivers', null=True, blank=True,
                               on_delete=models.SET_NULL, limit_choices_to={'role': 'driver'}, verbose_name='Driver')
    pickup_address = models.CharField(
        max_length=255, verbose_name='Pick-Up Address')
    droppoff_address = models.CharField(
        max_length=255, verbose_name='Dropp-Off Address')
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"
