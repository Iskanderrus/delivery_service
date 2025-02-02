import logging
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
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
