from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q

from .models import CustomUser, Order, OrderItem, Product
from .serializers import OrderSerializer


def customer_user_required(view_func):
    return user_passes_test(lambda u: getattr(u, "role", None) == "customer")(view_func)


@customer_user_required
@login_required
def create_order_from_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check if the customer has an address
    customer_profile = getattr(request.user, "customer_profile", None)
    if not customer_profile or not customer_profile.address:
        return JsonResponse(
            {"error": "You must have an address to create an order."}, status=400
        )

    # Get shop's address (pickup location)
    shop_profile = getattr(product.shop, "shop_profile", None)
    if not shop_profile or not shop_profile.address:
        return JsonResponse(
            {"error": "Product shop does not have a valid address."}, status=400
        )

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity <= 0:
            raise ValueError("Quantity must be a positive number.")
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid quantity provided."}, status=400)

    total_price = product.price * quantity

    # Check for an existing order with status "created"
    existing_order = Order.objects.filter(
        customer=request.user, status="created"
    ).first()

    if existing_order and existing_order.shop == product.shop:
        # Add item to existing order
        OrderItem.objects.create(
            order=existing_order,
            product=product,
            quantity=quantity,
            total_price=total_price,
        )
        existing_order.total_amount += total_price
        existing_order.save()

        return JsonResponse(
            {"message": "Item added to existing order.", "order_id": existing_order.id},
            status=200,
        )

    # Create a new order
    order = Order.objects.create(
        shop=product.shop,
        customer=request.user,
        pickup_address=shop_profile.address,
        dropoff_address=customer_profile.address,
        total_amount=total_price,
        status="created",
    )

    OrderItem.objects.create(
        order=order, product=product, quantity=quantity, total_price=total_price
    )

    return JsonResponse(
        {"message": "Order created successfully!", "order_id": order.id}, status=201
    )


@api_view(["GET", "POST"])
def order_list(request):
    if request.method == "GET":
        role = getattr(request.user, "role", None)

        if request.user.is_superuser:
            orders = Order.objects.all()
        elif role == "customer":
            orders = Order.objects.filter(customer=request.user)
        elif role == "shop":
            orders = Order.objects.filter(shop=request.user)
        elif role == "driver":
            orders = Order.objects.filter(driver=request.user)
        else:
            orders = Order.objects.none() 

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        if getattr(request.user, "role", None) == "customer":
            serializer = OrderSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(customer=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"error": "Only customers can create orders."},
            status=status.HTTP_403_FORBIDDEN,
        )
