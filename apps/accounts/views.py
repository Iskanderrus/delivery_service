import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from rest_framework import permissions, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from apps.accounts.forms import CustomUserCreationForm, LoginForm

from .models import CustomUser
from .serializers import CustomUserSerializer

logger = logging.getLogger(__name__)

def index_page(request):
    users = CustomUser.objects.all()
    return render(request, "accounts/index.html", {"users": users})


class CustomUserViewSet(viewsets.ModelViewSet):

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action in ["update", "partial_update", "retrieve", "destroy"]:
            return [permissions.IsAuthenticated()]
        elif self.action == "list":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        user = serializer.save()
        password = serializer.validated_data.get("password")
        if password:
            user.set_password(password)
            user.save()

    def perform_update(self, serializer):
        user = serializer.save()
        password = serializer.validated_data.get("password")
        if password:
            user.set_password(password)
            user.save()

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


def register_page(request):
    form = CustomUserCreationForm()
    return render(request, "accounts/auth/register.html", {"form": form})


def register_user(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            response = HttpResponse(status=204)
            response["HX-Redirect"] = "/"
            return response
        else:
            logger.debug(f"Form errors: {form.errors}")
            logger.debug(f"Request POST: {request.POST}")
            # Return just the form HTML fragment
            form_html = render_to_string(
                "accounts/auth/partials/register_form.html", {"form": form}, request
            )
            return JsonResponse({"success": False, "form_html": form_html}, status=400)
    return JsonResponse({"success": False}, status=400)


def login_page(request):
    form = LoginForm()
    return render(request, "accounts/auth/login.html", {"form": form})


def login_user(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("/")
        else:
            messages.error(request, "Invalid username or password.")
            # Return just the form HTML fragment
            form = LoginForm(request.POST)
            form_html = render_to_string(
                "accounts/auth/partials/login_form.html", {"form": form}, request
            )
            return JsonResponse({"success": False, "form_html": form_html}, status=400)
    else:
        return JsonResponse({"success": False}, status=400)


@login_required
def logout_user(request):
    logout(request)
    return redirect("/")


def user_list_page(request):
    users = CustomUser.objects.all()
    return render(request, "accounts/user_list.html", {"users": users})


def htmx_user_list(request):
    """Returns a partial HTML template with the list of users for HTMX"""
    users = CustomUser.objects.all()
    return render(request, "accounts/partials/user_list.html", {"users": users})


def htmx_user_detail(request, pk):
    """Returns partial HTML template for user details for HTMX"""
    user = get_object_or_404(CustomUser, pk=pk)
    return render(request, "accounts/partials/user_detail.html", {"user": user})


def htmx_user_create(request):
    """Handles user creation via HTMX"""
    if request.method == "POST":
        data = request.POST
        # Manually hash the password before saving
        password = data.get("password")
        if password:
            data["password"] = make_password(
                password
            )  # Django's make_password function hashes the password

        serializer = CustomUserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return render(request, "accounts/partials/user_row.html", {"user": user})
        return JsonResponse(
            {"error": "Invalid data", "details": serializer.errors}, status=400
        )
    return JsonResponse({"error": "Invalid request method"}, status=405)


@api_view(["PUT"])
def htmx_user_update(request, pk):
    """Handles user update via HTMX"""
    user = get_object_or_404(CustomUser, pk=pk)
    data = JSONParser().parse(request)
    serializer = CustomUserSerializer(user, data=data, partial=True)
    if serializer.is_valid():
        user = serializer.save()
        return render(request, "accounts/partials/user_row.html", {"user": user})
    return JsonResponse(
        {"error": "Invalid data", "details": serializer.errors}, status=400
    )


@api_view(["DELETE"])
def htmx_user_delete(request, pk):
    """Handles user deletion via HTMX"""
    user = get_object_or_404(CustomUser, pk=pk)
    user.is_active = False
    user.save()
    users = CustomUser.objects.all()
    return render(request, "accounts/partials/user_list.html", {"users": users})
