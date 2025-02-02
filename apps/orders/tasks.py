from Celery import shared_task

from apps.accounts.models import CustomUser
from apps.orders.models import Order


@shared_task
def assign_driver(order_id):
    order = Order.objects.get(id=order_id)
    available_driver = (
        CustomUser.objects.filter(role="driver")
        .filter(driver_profile__capacity__gte=order.total_weight)
        .first()
    )
    if available_driver:
        order.driver = available_driver
        order.status = "assigned"
        order.save()
