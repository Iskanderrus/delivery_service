from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DataError
from django.test import TestCase


class UserTestCase(TestCase):

    def test_create_superuser_success(self):
        """Verify superuser creation."""
        db = get_user_model()
        superuser = db.objects.create_superuser(
            username="test_name",
            email="super@user.com",
            first_name="First Name",
            password="Str0ngP@ssw0rd123",
        )
        self.assertTrue(
            superuser.is_superuser, "Superuser should have is_superuser=True"
        )
        self.assertTrue(superuser.is_staff, "Superuser should have is_staff=True")
        self.assertTrue(
            superuser.check_password("Str0ngP@ssw0rd123"), "Password should match"
        )
        self.assertEqual(superuser.email, "super@user.com", "Email should match")
        self.assertEqual(superuser.username, "test_name", "Username should match")
        self.assertEqual(superuser.first_name, "First Name", "First name should match")
        self.assertEqual(superuser.role, "admin", "Role should be 'admin'")
        self.assertTrue(superuser.is_active, "Superuser should be active")
        self.assertEqual(
            str(superuser), "test_name", "String representation should be username"
        )

    def test_create_superuser_without_permissions(self):
        """Ensure superuser creation requires is_superuser and is_staff."""
        db = get_user_model()
        with self.assertRaises(ValueError):
            db.objects.create_superuser(
                username="test_name",
                email="test@user.com",
                first_name="First Name",
                password="Str0ngP@ssw0rd123",
                is_superuser=False,
            )
        with self.assertRaises(ValueError):
            db.objects.create_superuser(
                username="test_name",
                email="test@user.com",
                first_name="First Name",
                password="Str0ngP@ssw0rd123",
                is_staff=False,
            )

    def test_create_user_missing_email(self):
        """Ensure email is required for user creation."""
        db = get_user_model()
        with self.assertRaises(ValueError):
            db.objects.create_user(
                email=None,
                username="user_without_email",
                first_name="Test",
                password="Str0ngP@ssw0rd123",
            )

    def test_create_user_with_invalid_email(self):
        """Ensure email format is validated."""
        db = get_user_model()
        with self.assertRaises(ValueError):
            db.objects.create_user(
                email="invalid-email",
                username="invalid_email_user",
                first_name="Test",
                password="Str0ngP@ssw0rd123",
            )

    def test_create_user_missing_username(self):
        """Ensure username is required for user creation."""
        db = get_user_model()
        with self.assertRaises(ValueError):
            db.objects.create_user(
                email="valid@user.com",
                username="",
                first_name="Test",
                password="Str0ngP@ssw0rd123",
            )

    def test_create_user_with_duplicate_username(self):
        """Ensure usernames are unique."""
        db = get_user_model()
        db.objects.create_user(
            email="user1@test.com",
            username="uniqueusername",
            first_name="Test",
            password="Str0ngP@ssw0rd123",
        )
        with self.assertRaises(ValueError):
            db.objects.create_user(
                email="user2@test.com",
                username="uniqueusername",
                first_name="Test",
                password="Str0ngP@ssw0rd123",
            )

    def test_create_user_with_invalid_role(self):
        """Ensure invalid roles raise an error."""
        db = get_user_model()
        with self.assertRaises(ValueError):
            db.objects.create_user(
                email="user3@test.com",
                username="user_with_invalid_role",
                first_name="Test",
                password="Str0ngP@ssw0rd123",
                role="invalid_role",
            )

    def test_default_user_role(self):
        """Verify default user role is 'shop'."""
        db = get_user_model()
        user = db.objects.create_user(
            email="user@test.com",
            username="user1",
            first_name="Test",
            password="Str0ngP@ssw0rd123",
        )
        self.assertEqual(user.role, "shop", "Default role should be 'shop'")

    def test_user_is_not_active(self):
        """Verify is_active can be set to False."""
        db = get_user_model()
        user = db.objects.create_user(
            email="user@test.com",
            username="user2",
            first_name="Test",
            password="Str0ngP@ssw0rd123",
            is_active=False,
        )
        self.assertFalse(user.is_active, "User should not be active")

    def test_create_user_missing_first_name(self):
        """Ensure first_name is required for user creation."""
        db = get_user_model()
        with self.assertRaises(ValueError):
            db.objects.create_user(
                email="user@test.com",
                username="user_without_first_name",
                first_name="",
                password="Str0ngP@ssw0rd123",
            )

    def test_create_user_without_password(self):
        """Ensure password is required for user creation."""
        db = get_user_model()
        with self.assertRaises(ValueError):
            db.objects.create_user(
                email="user@test.com",
                username="user_without_password",
                first_name="Test",
                password="",
            )

    def test_create_user_with_long_username(self):
        """Ensure username length is validated."""
        db = get_user_model()
        long_username = "a" * 151
        with self.assertRaises((ValidationError, DataError)):
            db.objects.create_user(
                email="user@test.com",
                username=long_username,
                first_name="Test",
                password="Str0ngP@ssw0rd123",
            )

    @patch("apps.accounts.models.logger")
    def test_invalid_password(self, mock_logger):
        """Ensure invalid passwords are logged."""
        invalid_password = "password"
        username = "testuser"
        db = get_user_model()
        with self.assertRaises(ValueError):
            db.objects.create_user(
                email="testuser@test.com",
                username=username,
                first_name="Test",
                password=invalid_password,
            )
        mock_logger.error.assert_called_with(
            f"Invalid password for user {username}: ['This password is too common.']"
        )

    @patch("apps.accounts.models.logger")
    def test_create_superuser_with_exception(self, mock_logger):
        """Ensure superuser creation exceptions are logged."""
        username = "testsuperuser"
        email = "testsuperuser@test.com"
        password = "Str0ngP@ssw0rd123"
        role = "admin"
        db = get_user_model()
        with patch.object(
            db.objects,
            "create_user",
            side_effect=Exception("Custom error during user creation"),
        ):
            with self.assertRaises(Exception):
                db.objects.create_superuser(
                    email=email,
                    username=username,
                    first_name="Super",
                    password=password,
                    role=role,
                )
        mock_logger.error.assert_called_once_with(
            f"Error creating superuser '{username}' - Custom error during user creation"
        )
