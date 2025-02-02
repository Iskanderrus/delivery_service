import logging

from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, first_name, password, role=None, **kwargs):
        if not email:
            logger.error("Email is required.")
            raise ValueError(_("Email is required."))
        if not username or not username.strip():
            logger.error("Username is required and cannot be empty.")
            raise ValueError(_("Username is required and cannot be empty."))
        if not first_name:
            logger.error("First name is required.")
            raise ValueError(_("First name is required."))
        if not password:
            logger.error("Password is required.")
            raise ValueError(_("Password is required."))

        email = self.normalize_email(email)

        try:
            validate_email(email)
        except ValidationError as e:
            logger.error(f"Invalid email format: {email} - {e}")
            raise ValueError(_("Invalid email format."))

        try:
            validate_password(password)
        except ValidationError as e:
            logger.error(f"Invalid password for user {username}: {e}")
            raise ValueError(_("Invalid password format."))

        if self.model.objects.filter(username__iexact=username).exists():
            logger.error(f"Username '{username}' already exists.")
            raise ValueError(_("A user with this username already exists."))

        role = role or "shop"

        # Use Django's built-in validation for choices instead of manually checking
        if role not in [choice[0] for choice in self.model.ROLE_CHOICES]:
            logger.error(f"Invalid role: {role}")
            raise ValueError(_("Invalid role selected."))

        user = self.model(
            email=email,
            username=username.lower(),
            first_name=first_name,
            role=role,
            **kwargs,
        )
        user.set_password(password)

        try:
            user.save(using=self._db)
            logger.info(f"User '{username}' created successfully with role: {role}.")
        except Exception as e:
            logger.error(f"Error saving user '{username}' - {e}")
            raise

        return user

    def create_superuser(self, email, username, first_name, password, **kwargs):
        kwargs.setdefault("role", "admin")
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        if not kwargs.get("is_staff"):
            logger.error(f"Superuser must have 'is_staff' set to True: {email}")
            raise ValueError(_('Superuser must have "is_staff" set to True.'))
        if not kwargs.get("is_superuser"):
            logger.error(f"Superuser must have 'is_superuser' set to True: {email}")
            raise ValueError(_('Superuser must have "is_superuser" set to True.'))

        try:
            user = self.create_user(
                email=email,
                username=username,
                first_name=first_name,
                password=password,
                **kwargs,
            )
            logger.info(
                f"Superuser '{username}' created successfully with role: {kwargs['role']}."
            )
            return user
        except Exception as e:
            logger.error(f"Error creating superuser '{username}' - {e}")
            raise


class CustomUser(AbstractUser, PermissionsMixin):
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]
        indexes = [models.Index(fields=["email", "username"])]
        constraints = [
            CheckConstraint(
                check=Q(
                    role__in=[
                        choice[0]
                        for choice in [
                            ("shop", "Shop"),
                            ("driver", "Driver"),
                            ("admin", "Admin"),
                            ("customer", "Customer"),
                        ]
                    ]
                ),
                name="role_check",
            )
        ]

    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(_("username"), max_length=150, unique=True)
    first_name = models.CharField(_("first name"), max_length=100)
    last_name = models.CharField(_("last name"), max_length=100, null=True, blank=True)
    company_name = models.CharField(
        _("company name"), max_length=150, blank=True, null=True
    )

    ROLE_CHOICES = [
        ("shop", "Shop"),
        ("driver", "Driver"),
        ("admin", "Admin"),
        ("customer", "Customer"),
    ]
    role = models.CharField(
        _("role"), max_length=10, choices=ROLE_CHOICES, default="shop"
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name"]

    def __str__(self):
        return self.username


class DriverProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="driver_profile",
        limit_choices_to={"role": "driver"},
    )
    vehicle_type = models.CharField(max_length=50)
    capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Capacity in kg or liters",
        default=10,
    )

    def clean(self):
        if self.user.role != "driver":
            raise ValidationError(
                "Only users with the 'driver' role can have a DriverProfile."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.vehicle_type}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        limit_choices_to={"role": "customer"},
    )
    payment_methods = models.JSONField(
        help_text="List of payment methods", default=list
    )

    def clean(self):
        if self.user.role != "customer":
            raise ValidationError("User role must be 'customer' for CustomerProfile.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - Customer"


def get_category_model():
    from apps.products.models import Category

    return Category


class ShopProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="shop_profile",
        limit_choices_to={"role": "shop"},
    )
    product_categories = models.ManyToManyField(get_category_model(), blank=True)
    accepted_payment_methods = models.JSONField(
        help_text="Accepted payment methods", default=list
    )

    def clean(self):
        if self.user.role != "shop":
            raise ValidationError(
                "Only users with the 'shop' role can have a ShopProfile."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - Shop"
