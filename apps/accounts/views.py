import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods, require_POST
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.forms import (
    CustomUserCreationForm,
    CustomerProfileForm,
    DriverProfileForm,
    LoginForm,
    ShopProfileForm,
)

from .models import CustomUser
from .serializers import CustomUserSerializer

logger = logging.getLogger(__name__)


def index_page(request):
    return render(request, "accounts/index.html")


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


@require_POST
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
            form_html = render_to_string(
                "accounts/auth/partials/register_form.html", {"form": form}, request
            )
            return JsonResponse({"success": False, "form_html": form_html}, status=400)
    return JsonResponse({"success": False}, status=400)


def login_page(request):
    form = LoginForm()
    return render(request, "accounts/auth/login.html", {"form": form})


@require_POST
def login_user(request):
    form = LoginForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            response = HttpResponse(status=204)
            response["HX-Redirect"] = "/"
            return response
        else:
            messages.error(request, "Invalid login credentials")
    else:
        messages.error(request, "Invalid form")

    form_html = render_to_string(
        "accounts/auth/partials/login_form.html", {"form": form}, request
    )
    return JsonResponse({"success": False, "form_html": form_html}, status=400)


@login_required
def logout_user(request):
    logout(request)
    return redirect("/")


def user_list_page(request):
    if request.user.is_authenticated():
        if request.user.is_superuser():
            users = CustomUser.objects.filter(is_active=True).exclude(role="admin")
    return render(request, "accounts/user_list.html", {"users": users})


def htmx_user_list(request):
    """Returns a list of users via HTMX, filtered to active users, only for superusers"""
    if request.user.is_superuser:
        users = CustomUser.objects.filter(is_active=True).exclude(role="admin")
        return render(request, "accounts/partials/user_list.html", {"users": users})
    else:
        return HttpResponseForbidden("You do not have permission to view this page.")


def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)

    profile = None
    if user.role == "driver":
        profile = getattr(user, "driver_profile", None)
    elif user.role == "customer":
        profile = getattr(user, "customer_profile", None)
    elif user.role == "shop":
        profile = getattr(user, "shop_profile", None)

    return render(
        request, "accounts/user_detail.html", {"user": user, "profile": profile}
    )


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@login_required
@superuser_required
def create_user(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")

            if CustomUser.objects.filter(username=username).exists():
                form.add_error("username", "A user with this username already exists.")
            elif CustomUser.objects.filter(email=email).exists():
                form.add_error("email", "A user with this email already exists.")
            else:
                user = form.save(commit=False)
                if user.is_superuser or user.is_staff:
                    messages.error(
                        request, "You cannot create a superuser with this form."
                    )
                else:
                    user.save()
                    messages.success(request, "User created successfully.")
                    users = CustomUser.objects.filter(is_active=True).exclude(
                        role="admin"
                    )

                    return render(
                        request,
                        "accounts/partials/user_list.html",
                        {"users": users, "close_modal": True},
                    )
    else:
        form = CustomUserCreationForm()

    return render(request, "admin/create_user.html", {"form": form})


@login_required
@superuser_required
def edit_user(request, pk):
    user = get_object_or_404(CustomUser, id=pk)

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            return render(request, "accounts/partials/user_row.html", {"user": user})

    else:
        form = CustomUserCreationForm(instance=user)

    return render(
        request,
        "accounts/partials/edit_user.html",
        {"form": form, "user": user},
    )

@login_required
@superuser_required
def edit_profile(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)

    if user.role == "driver":
        profile = getattr(user, "driver_profile", None)
        form_class = DriverProfileForm
    elif user.role == "customer":
        profile = getattr(user, "customer_profile", None)
        form_class = CustomerProfileForm
    elif user.role == "shop":
        profile = getattr(user, "shop_profile", None)
        form_class = ShopProfileForm
    else:
        return HttpResponse("Invalid user role", status=400)

    if request.method == "POST":
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return user_detail(request, pk)
    else:
        form = form_class(instance=profile)

    return render(
        request, "accounts/profile_edit_form.html", {"form": form, "user": user}
    )


@require_http_methods(["DELETE"])
def htmx_user_delete(request, pk):
    """Handles user deletion via HTMX"""
    user = get_object_or_404(CustomUser, pk=pk)
    user.is_active = False
    user.save()

    users = CustomUser.objects.filter(is_active=True)
    return render(request, "accounts/partials/user_list.html", {"users": users})
