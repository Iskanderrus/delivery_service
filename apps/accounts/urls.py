from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    create_user,
    htmx_user_delete,
    user_detail,
    htmx_user_list,
    edit_user,
    index_page,
    login_page,
    login_user,
    logout_user,
    register_page,
    register_user,
    user_list_page,
)

app_name = "accounts"

# Create a router for the API viewset
router = DefaultRouter()
router.register(r"users", CustomUserViewSet)

urlpatterns = [
    path("", index_page, name="index"),
    path("accounts/", include(router.urls)),  # API
    path("accounts/users/", user_list_page, name="user-list-page"),
    # registration/authorization
    path("accounts/register/", register_page, name="register"),
    path("accounts/register-user/", register_user, name="register_user"),
    path("accounts/login/", login_page, name="login"),
    path("accounts/login-user/", login_user, name="login_user"),
    path("accounts/logout/", logout_user, name="logout"),
    # HTMX URLs for user actions
    path("users/<int:pk>/user_detail/", user_detail, name="user_detail"),
    path("users/htmx_list/", htmx_user_list, name="htmx_user_list"),
    path("users/create_user/", create_user, name="create_user"),

    path("users/edit_user/<int:pk>/", edit_user, name="edit_user"),
    path("users/htmx_delete/<int:pk>/", htmx_user_delete, name="htmx_user_delete"),
]
