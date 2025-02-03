from decimal import Decimal
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from apps.accounts.models import CustomUser
from apps.orders.models import (
    Order,
    OrderItem,
    get_coordinates,
    get_distance,
)
from apps.products.models import Product
import time
import openrouteservice
import redis
from redis.exceptions import ConnectionError


def wait_for_redis(host="redis", port=6379, timeout=10):
    """Waits for the Redis server to be available before tests start."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            redis_client = redis.StrictRedis(host=host, port=port, db=1)
            redis_client.ping()
            return
        except ConnectionError:
            time.sleep(0.5)
    raise Exception(f"Timeout waiting for Redis at {host}:{port}")


class OrderTests(TestCase):
    """Test suite for the Order and OrderItem models."""

    def setUp(self):
        """Set up test data for each test method."""
        # Ensure Redis is ready before tests start.
        wait_for_redis()

        # Create a default supplier user
        self.supplier = CustomUser.objects.create(
            username="testsupplier",
            password="testpassword",
            role="shop",
            email="testsupplier@example.com",
        )
        # Create a default shop user
        self.shop = CustomUser.objects.create(
            username="testshop",
            password="testpassword",
            role="shop",
            email="testshop@example.com",
        )
        # Create a default driver user
        self.driver = CustomUser.objects.create(
            username="testdriver",
            password="testpassword",
            role="driver",
            email="testdriver@example.com",
        )
        # Create a default customer user
        self.customer = CustomUser.objects.create(
            username="testcustomer",
            password="testpassword",
            role="customer",
            email="testcustomer@example.com",
        )
        # Create a test product
        self.product = Product.objects.create(
            name="Test Product", price=10.00, weight=2.00, supplier=self.supplier
        )

        self.order = Order.objects.create(
            shop=self.shop,
            pickup_address="123 Test St",
            dropoff_address="456 Test Ave",
            customer=self.customer,
        )

    def test_order_creation(self):
        """Test the creation of a basic order."""

        self.assertEqual(self.order.status, "created")
        self.assertEqual(self.order.shop, self.shop)
        self.assertEqual(self.order.customer, self.customer)
        self.assertIsNone(self.order.total_amount)
        self.assertIsNone(self.order.delivery_price)

    def test_order_item_creation(self):
        """Test the creation of an order item"""
        order_item = OrderItem.objects.create(
            product=self.product, quantity=2, order=self.order
        )

        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.total_price, 20.00)
        self.assertEqual(order_item.order, self.order)

    def test_order_item_total_price_calculation_on_save(self):
        """Test the total price calculation of OrderItem on save method."""
        order_item = OrderItem(product=self.product, quantity=3, order=self.order)
        order_item.save()
        self.assertEqual(order_item.total_price, Decimal(30.00))

        order_item.quantity = 4
        order_item.save()
        self.assertEqual(order_item.total_price, Decimal(40.00))

    def test_order_str_method(self):
        """Test the __str__ method for Order."""
        self.assertEqual(
            str(self.order), f"Order {self.order.id} - {self.order.status}"
        )

    def test_calculate_delivery_price_with_valid_addresses(self):
        """Test delivery price calculation with valid addresses."""

        with patch("apps.orders.models.get_distance", return_value=10.0):
            delivery_price = self.order.calculate_delivery_price()
            self.assertEqual(delivery_price, Decimal(20.00))
            self.assertEqual(self.order.delivery_price, Decimal(20.00))

    def test_calculate_delivery_price_with_no_coordinates(self):
        """Test delivery price when address lookup fails."""

        with patch("apps.orders.models.get_distance", return_value=None):
            delivery_price = self.order.calculate_delivery_price()
            self.assertEqual(delivery_price, Decimal(0))
            self.assertEqual(self.order.delivery_price, Decimal(0))

    def test_calculate_delivery_price_with_weight_surcharge(self):
        """Test delivery price calculation with weight surcharge."""
        self.order.total_weight = 10
        with patch("apps.orders.models.get_distance", return_value=10):
            delivery_price = self.order.calculate_delivery_price()
            self.assertEqual(delivery_price, Decimal(25.00))
            self.assertEqual(self.order.delivery_price, Decimal(25.00))

    def test_calculate_delivery_price_with_zero_weight(self):
        """Test delivery price calculation with zero weight."""
        self.order.total_weight = 0
        with patch("apps.orders.models.get_distance", return_value=10):
            delivery_price = self.order.calculate_delivery_price()
            self.assertEqual(delivery_price, Decimal(20.00))
            self.assertEqual(self.order.delivery_price, Decimal(20.00))


class GeocodingTests(TestCase):
    """Test suite for geocoding functionality."""

    def setUp(self):
        """Set up settings before testing."""
        self.api_key = "test_api_key"
        settings.ORS_API_KEY = self.api_key

    def test_get_coordinates_success(self):
        """Test successful address to coordinates conversion."""
        mock_response = {"features": [{"geometry": {"coordinates": [10.0, 20.0]}}]}
        with patch(
            "openrouteservice.client.Client.geocode", return_value=mock_response
        ) as mock_geocode:
            client = openrouteservice.Client(key=self.api_key)
            coordinates = get_coordinates("Test Address")
            mock_geocode.assert_called_once()
            self.assertEqual(coordinates, [10.0, 20.0])

    def test_get_coordinates_no_features(self):
        """Test coordinate retrieval when no features are returned."""
        mock_response = {"features": []}
        with patch(
            "openrouteservice.client.Client.geocode", return_value=mock_response
        ) as mock_geocode:
            client = openrouteservice.Client(key=self.api_key)
            coordinates = get_coordinates("Test Address")
            mock_geocode.assert_called_once()
            self.assertIsNone(coordinates)

    def test_get_coordinates_none_response(self):
        """Test coordinate retrieval when no response returned."""
        with patch(
            "openrouteservice.client.Client.geocode", return_value=None
        ) as mock_geocode:
            client = openrouteservice.Client(key=self.api_key)
            coordinates = get_coordinates("Test Address")
            mock_geocode.assert_called_once()
            self.assertIsNone(coordinates)

    def test_get_coordinates_invalid_response(self):
        """Test coordinate retrieval when no response is invalid."""
        mock_response = "invalid response"
        with patch(
            "openrouteservice.client.Client.geocode", return_value=mock_response
        ) as mock_geocode:
            client = openrouteservice.Client(key=self.api_key)
            coordinates = get_coordinates("Test Address")
            mock_geocode.assert_called_once()
            self.assertIsNone(coordinates)

    def test_get_coordinates_exception(self):
        """Test error handling when exception occurs while geocoding."""
        with patch(
            "openrouteservice.client.Client.geocode",
            side_effect=Exception("Test Exception"),
        ) as mock_geocode:
            client = openrouteservice.Client(key=self.api_key)
            coordinates = get_coordinates("Test Address")
            mock_geocode.assert_called_once()
            self.assertIsNone(coordinates)


class DistanceTests(TestCase):
    """Test suite for distance calculation functionality."""

    def setUp(self):
        self.api_key = "test_api_key"
        settings.ORS_API_KEY = self.api_key

    def test_get_distance_success(self):
        """Test successful distance calculation."""
        mock_coords = [10.0, 20.0]
        mock_route = {"features": [{"properties": {"segments": [{"distance": 10000}]}}]}

        with patch("apps.orders.models.get_coordinates", return_value=mock_coords):
            with patch(
                "openrouteservice.Client.directions", return_value=mock_route
            ) as mock_directions:
                distance = get_distance("pickup_address", "dropoff_address")
                mock_directions.assert_called_once()
                self.assertEqual(distance, 10.0)

    def test_get_distance_coordinate_lookup_fails(self):
        """Test distance calculation when coordinate lookup fails."""

        with patch("apps.orders.models.get_coordinates", return_value=None):
            distance = get_distance("pickup_address", "dropoff_address")
            self.assertIsNone(distance)

    def test_get_distance_directions_exception(self):
        """Test exception when getting directions."""
        mock_coords = [10.0, 20.0]
        with patch("apps.orders.models.get_coordinates", return_value=mock_coords):
            with patch(
                "openrouteservice.Client.directions",
                side_effect=Exception("Test Exception"),
            ) as mock_directions:
                distance = get_distance("pickup_address", "dropoff_address")
                mock_directions.assert_called_once()
                self.assertIsNone(distance)

    def test_get_distance_invalid_route_data(self):
        """Test when the route data is invalid"""
        mock_coords = [10.0, 20.0]
        mock_route = {"features": []}
        with patch("apps.orders.models.get_coordinates", return_value=mock_coords):
            with patch(
                "openrouteservice.Client.directions", return_value=mock_route
            ) as mock_directions:
                distance = get_distance("pickup_address", "dropoff_address")
                mock_directions.assert_called_once()
                self.assertIsNone(distance)

    def test_get_distance_invalid_key(self):
        """Test when the route data has the incorrect key"""
        mock_coords = [10.0, 20.0]
        mock_route = {"features": [{"invalid_key": [{"distance": 10000}]}]}
        with patch("apps.orders.models.get_coordinates", return_value=mock_coords):
            with patch(
                "openrouteservice.Client.directions", return_value=mock_route
            ) as mock_directions:
                distance = get_distance("pickup_address", "dropoff_address")
                mock_directions.assert_called_once()
                self.assertIsNone(distance)
