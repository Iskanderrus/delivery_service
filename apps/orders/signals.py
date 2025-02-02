from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import OrderItem


@receiver(post_save, sender=OrderItem)
def update_order_totals(sender, instance, created, **kwargs):
    order = instance.order

    total_amount = sum(item.total_price for item in order.items.all())
    total_weight = sum(
        item.product.weight * item.quantity for item in order.items.all()
    )

    order.total_amount = total_amount
    order.total_weight = total_weight
    order.save()
