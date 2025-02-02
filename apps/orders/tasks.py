from __future__ import absolute_import

from celery import shared_task
from celery.exceptions import TaskRetry

from apps.accounts.models import CustomUser
from apps.orders.models import Order


@shared_task
def assign_driver(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise TaskRetry("Order not found", exc=None)

    # Check if the order is really in 'ready_to_collect' status
    if order.status != "ready_to_collect":
        raise TaskRetry(
            f"Order {order_id} is not in 'ready_to_collect' status", exc=None
        )

    # Check for available drivers, who have no other orders in status 'assigned' or 'in_transit'
    available_driver = (
        CustomUser.objects.filter(role="driver")
        .exclude(driver_orders__status__in=["assigned", "in_transit"])
        .filter(driver_profile__capacity__gte=order.total_weight)
        .first()
    )

    if available_driver:
        order.driver = available_driver
        order.status = "assigned"
        order.save()
    else:
        raise TaskRetry("No available driver for the order", exc=None)
