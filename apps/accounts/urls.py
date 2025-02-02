from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    htmx_user_create,
    htmx_user_delete,
    htmx_user_detail,
    htmx_user_list,
    htmx_user_update,
    index_page,
    login_page,
    login_user,
    logout_user,
    register_page,
    register_user,
    user_list_page,
)

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
    path("users/<int:pk>/htmx_detail/", htmx_user_detail, name="htmx_user_detail"),
    path("users/htmx_list/", htmx_user_list, name="htmx_user_list"),
    path("users/htmx_create/", htmx_user_create, name="htmx_user_create"),
    path("users/htmx_update/<int:pk>/", htmx_user_update, name="htmx_user_update"),
    path("users/htmx_delete/<int:pk>/", htmx_user_delete, name="htmx_user_delete"),
]
