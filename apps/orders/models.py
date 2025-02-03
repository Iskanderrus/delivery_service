import logging
from decimal import Decimal
from typing import Dict, List, Optional

import openrouteservice
import redis
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import CustomUser
from apps.products.models import Product

logger = logging.getLogger(__name__)

ORS_API_KEY = settings.ORS_API_KEY
DELIVERY_PRICE_PER_KM = getattr(settings, "DELIVERY_PRICE_PER_KM", 2.00)
REDIS_HOST = getattr(settings, "REDIS_HOST", "127.0.0.1")
REDIS_PORT = getattr(settings, "REDIS_PORT", 6379)


# Create a Redis client for caching distance calculations
redis_client = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True
)


def get_coordinates(address: str) -> Optional[List[float]]:
    """Convert an address to latitude/longitude using OpenRouteService."""
    client = openrouteservice.Client(key=ORS_API_KEY)
    try:
        response = client.geocode(address)
    except Exception as e:
        logger.error(f"Error geocoding address '{address}': {e}")
        return None

    if isinstance(response, dict) and response.get("features"):
        features = response["features"]
        if features:
            return features[0]["geometry"]["coordinates"]
        else:
            logger.warning(f"No coordinates found for address '{address}'")
            return None
    else:
        logger.error(
            f"Invalid response received for geocoding address '{address}': {response}"
        )
        return None


def get_distance(pickup_address: str, dropoff_address: str) -> Optional[float]:
    """
    Calculate the distance between two addresses using OpenRouteService,
    caching results in Redis.
    """
    cache_key = f"distance:{pickup_address}:{dropoff_address}"

    # Check if distance is already cached
    cached_distance = redis_client.get(cache_key)
    if cached_distance:
        return float(cached_distance)

    client = openrouteservice.Client(key=ORS_API_KEY)

    pickup_coords = get_coordinates(pickup_address)
    dropoff_coords = get_coordinates(dropoff_address)

    if not pickup_coords or not dropoff_coords:
        logger.warning(
            f"Could not fetch coordinates for pickup '{pickup_address}' or dropoff '{dropoff_address}'"
        )
        return None  # Address lookup failed

    try:
        route = client.directions(
            coordinates=[pickup_coords, dropoff_coords],
            profile="driving-car",
            format="geojson",
        )
    except Exception as e:
        logger.error(
            f"Error getting directions between '{pickup_address}' and '{dropoff_address}': {e}"
        )
        return None

    try:
        distance_km = (
            route["features"][0]["properties"]["segments"][0]["distance"] / 1000
        )
    except (KeyError, IndexError, TypeError) as e:
        logger.error(
            f"Error parsing route data between '{pickup_address}' and '{dropoff_address}': {e}"
        )
        return None

    # Cache distance for 24 hours
    redis_client.setex(cache_key, 86400, distance_km)

    return distance_km


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
        ("ready_to_collect", _("Order ready to collect")),
        ("assigned", _("Order assigned")),
        ("in_transit", _("Order in transit")),
        ("delivered", _("Order delivered")),
    ]
    total_amount = models.DecimalField(
        _("Total amount"), max_digits=10, decimal_places=10, null=True, blank=True
    )
    delivery_price = models.DecimalField(
        _("Delivery price"), max_digits=10, decimal_places=10, null=True, blank=True
    )
    total_weight = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1000.0)],
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

    def __str__(self) -> str:
        return f"Order {self.id} - {self.status}"

    def calculate_delivery_price(self) -> Optional[Decimal]:
        """
        Calculates the delivery price for the order.

        Returns:
            Optional[Decimal]: The total delivery price if the distance
                              can be calculated, otherwise returns None
        """
        distance_km = get_distance(self.pickup_address, self.dropoff_address)
        if distance_km is None:
            logger.warning(
                f"Could not calculate distance for order {self.id}, setting delivery price to 0"
            )
            self.delivery_price = Decimal(0)
            self.save()
            return Decimal(0)

        weight_surcharge = (
            Decimal(0.5) * Decimal(self.total_weight)
            if self.total_weight > 5
            else Decimal(0)
        )
        distance_price = Decimal(DELIVERY_PRICE_PER_KM) * Decimal(distance_km)
        total_delivery_price = distance_price + weight_surcharge

        self.delivery_price = total_delivery_price
        self.save()
        return total_delivery_price
