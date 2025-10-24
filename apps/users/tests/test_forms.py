"""Tests for user forms."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.users import factories, forms

User = get_user_model()


class UserCreateFormTest(TestCase):
    """Test cases for UserCreateForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.group = Group.objects.create(name="Test Group")

    def test_valid_form(self) -> None:
        """Test form with valid data."""
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "groups": [self.group.pk],
        }
        form = forms.UserCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self) -> None:
        """Test form validation when passwords don't match."""
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirm_password": "DifferentPass123!",
            "groups": [self.group.pk],
        }
        form = forms.UserCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_password", form.errors)

    def test_duplicate_email(self) -> None:
        """Test form validation when email already exists."""
        factories.UserFactory(email="existing@example.com")

        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        }
        form = forms.UserCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_weak_password(self) -> None:
        """Test form validation with weak password."""
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "123",
            "confirm_password": "123",
        }
        form = forms.UserCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_missing_required_fields(self) -> None:
        """Test form validation with missing required fields."""
        form_data = {}
        form = forms.UserCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
        self.assertIn("last_name", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("password", form.errors)

    def test_save_creates_user_with_hashed_password(self) -> None:
        """Test that save method creates user with hashed password."""
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "groups": [self.group.pk],
        }
        form = forms.UserCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertIsNotNone(user.pk)
        self.assertTrue(user.check_password("SecurePass123!"))
        self.assertIn(self.group, user.groups.all())


class UserUpdateFormTest(TestCase):
    """Test cases for UserUpdateForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = factories.UserFactory(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )
        self.group = Group.objects.create(name="Test Group")

    def test_valid_form_without_password_change(self) -> None:
        """Test form with valid data and no password change."""
        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "test@example.com",
            "password": "",
            "confirm_password": "",
            "groups": [self.group.pk],
        }
        form = forms.UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_form_with_password_change(self) -> None:
        """Test form with valid data and password change."""
        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "test@example.com",
            "password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!",
            "groups": [self.group.pk],
        }
        form = forms.UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self) -> None:
        """Test form validation when passwords don't match."""
        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "test@example.com",
            "password": "NewSecurePass123!",
            "confirm_password": "DifferentPass123!",
            "groups": [self.group.pk],
        }
        form = forms.UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_password", form.errors)

    def test_duplicate_email_different_user(self) -> None:
        """Test form validation when email exists for different user."""
        factories.UserFactory(email="other@example.com")

        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "other@example.com",
            "password": "",
            "confirm_password": "",
        }
        form = forms.UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_same_email_same_user(self) -> None:
        """Test that same email is valid for same user."""
        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "test@example.com",
            "password": "",
            "confirm_password": "",
        }
        form = forms.UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_save_updates_user_without_password_change(self) -> None:
        """Test that save method updates user without changing password."""
        original_password = self.user.password

        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "test@example.com",
            "password": "",
            "confirm_password": "",
            "groups": [self.group.pk],
        }
        form = forms.UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.password, original_password)
        self.assertIn(self.group, user.groups.all())

    def test_save_updates_user_with_password_change(self) -> None:
        """Test that save method updates user and changes password."""
        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "test@example.com",
            "password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!",
            "groups": [self.group.pk],
        }
        form = forms.UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Smith")
        self.assertTrue(user.check_password("NewSecurePass123!"))
        self.assertIn(self.group, user.groups.all())

    def test_weak_password_update(self) -> None:
        """Test form validation with weak password during update."""
        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "test@example.com",
            "password": "123",
            "confirm_password": "123",
        }
        form = forms.UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)


class UserSettingsFormTest(TestCase):
    """Test cases for UserSettingsForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = factories.UserFactory(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )

    def test_valid_form(self) -> None:
        """Test form with valid data."""
        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
        }
        form = forms.UserSettingsForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_save_updates_user(self) -> None:
        """Test that save method updates user."""
        form_data = {
            "first_name": "Jane",
            "last_name": "Smith",
        }
        form = forms.UserSettingsForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Smith")

    def test_last_name_optional(self) -> None:
        """Test that last_name is optional."""
        form_data = {
            "first_name": "Jane",
            "last_name": "",
        }
        form = forms.UserSettingsForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
