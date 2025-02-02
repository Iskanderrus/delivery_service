from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CustomerProfile, DriverProfile, ShopProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'role', 'is_active', 'is_staff', 'is_superuser')

    search_fields = ('email', 'username', 'first_name', 'last_name')

    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': (('username', 'role'), ('first_name',
         'last_name'), 'company_name', ('is_active', 'is_staff', 'is_superuser'),)}),
        ('Permissions', {'fields': ('groups', 'user_permissions'), 'classes': (
            'collapse',), 'description': ('Permissions of the user and his user groups')}),
        ('Important dates', {'fields': (('last_login', 'date_joined'),)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    ordering = ('email',)

admin.site.register(CustomerProfile)
admin.site.register(DriverProfile)
admin.site.register(ShopProfile)
