from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import CustomerProfile, CustomUser, DriverProfile, ShopProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if instance.role == "driver":
        if created:
            DriverProfile.objects.create(user=instance)
        elif not hasattr(instance, "driver_profile"):
            DriverProfile.objects.create(user=instance)

    elif instance.role == "customer":
        if created:
            CustomerProfile.objects.create(user=instance)
        elif not hasattr(instance, "customer_profile"):
            CustomerProfile.objects.create(user=instance)

    elif instance.role == "shop":
        if created:
            ShopProfile.objects.create(user=instance)
        elif not hasattr(instance, "shop_profile"):
            ShopProfile.objects.create(user=instance)
