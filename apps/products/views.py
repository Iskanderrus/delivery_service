from django.db.models import Q
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from apps.products.models import Product
from apps.products.serializers import CategorySerializer, ProductSerializer

from .models import Category, Product


class CreateCategoryView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Ensure only shop users or admins can create categories."""
        if self.request.user.role not in ["shop", "admin"]:
            return Response(
                {"error": "Only shop users or admins can create categories."},
                status=HTTP_400_BAD_REQUEST,
            )
        serializer.save()


class CreateProductView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Ensures the supplier is set to the current user."""
        if self.request.user.role != "shop":
            return Response(
                {"error": "Only shop users can create products."},
                status=HTTP_400_BAD_REQUEST,
            )
        serializer.save(supplier=self.request.user)


class UpdateProductView(UpdateView):
    pass


class DeleteProductView(DeleteView):
    pass


class ProductListView(ListView):
    model = Product
    template_name = "product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Product.objects.all()

        elif self.request.user.role == "customer":
            return Product.objects.filter(is_active=True)

        elif self.request.user.role == "shop":
            return Product.objects.filter(supplier=self.request.user)

        return Product.objects.none()
