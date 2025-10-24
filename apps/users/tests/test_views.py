"""Tests for user views."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from apps.users import factories

User = get_user_model()


class UserListViewTest(TestCase):
    """Test cases for UserListView."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = factories.UserFactory()
        self.client.force_login(self.user)

        # Add view_user permission
        permission = Permission.objects.get(codename="view_user")
        self.user.user_permissions.add(permission)

        self.url = reverse("apps.users:user_list")

    def test_get_requires_login(self) -> None:
        """Test that view requires authentication."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/account/login/", response.url)

    def test_get_requires_permission(self) -> None:
        """Test that view requires view_user permission."""
        user_without_permission = factories.UserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_returns_200(self) -> None:
        """Test GET request returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/list.html")

    def test_lists_users(self) -> None:
        """Test that view lists all users."""
        # Give permission to view users
        permission = Permission.objects.get(codename="view_user")
        self.user.user_permissions.add(permission)

        user1 = factories.UserFactory(first_name="John", last_name="Doe")
        user2 = factories.UserFactory(first_name="Jane", last_name="Smith")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John")
        self.assertContains(response, "Jane")

    def test_filter_by_name(self) -> None:
        """Test filtering users by name."""
        user1 = factories.UserFactory(first_name="John", last_name="Doe")
        user2 = factories.UserFactory(first_name="Jane", last_name="Smith")

        response = self.client.get(self.url, {"name_search": "John"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John")

    def test_filter_by_active_status(self) -> None:
        """Test filtering users by active status."""
        active_user = factories.UserFactory(is_active=True, first_name="ActiveUser", last_name="Test")
        inactive_user = factories.UserFactory(
            is_active=False, first_name="InactiveUser", last_name="Test"
        )

        response = self.client.get(self.url, {"is_active": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ActiveUser")

    def test_pagination(self) -> None:
        """Test pagination works correctly."""
        for i in range(15):
            factories.UserFactory(first_name=f"User{i}")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # FilterView uses page_obj instead of is_paginated
        self.assertTrue(response.context["page_obj"].has_other_pages())
        self.assertEqual(len(response.context["users"]), 10)


class UserCreateViewTest(TestCase):
    """Test cases for UserCreateView."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = factories.StaffUserFactory()
        self.user.is_superuser = False
        self.user.save()
        self.client.force_login(self.user)

        # Add add_user permission
        permission = Permission.objects.get(codename="add_user")
        self.user.user_permissions.add(permission)

        self.group = Group.objects.create(name="Test Group")
        self.url = reverse("apps.users:user_create")

    def test_get_requires_login(self) -> None:
        """Test that view requires authentication."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_requires_permission(self) -> None:
        """Test that view requires add_user permission."""
        user_without_permission = factories.UserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_returns_200(self) -> None:
        """Test GET request returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/form.html")

    def test_post_creates_user(self) -> None:
        """Test POST request creates new user."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "groups": [self.group.pk],
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("apps.users:user_list"))

        # Verify user was created
        user = User.objects.get(email="john.doe@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("SecurePass123!"))
        self.assertIn(self.group, user.groups.all())

    def test_post_with_invalid_data(self) -> None:
        """Test POST with invalid data shows errors."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "password": "123",
            "confirm_password": "456",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        # Just verify form is not valid
        self.assertFalse(response.context["form"].is_valid())


class UserUpdateViewTest(TestCase):
    """Test cases for UserUpdateView."""

    def setUp(self) -> None:
        """Set up test data."""
        self.admin = factories.StaffUserFactory()
        self.admin.is_superuser = False
        self.admin.save()
        self.client.force_login(self.admin)

        # Add change_user permission
        permission = Permission.objects.get(codename="change_user")
        self.admin.user_permissions.add(permission)

        self.user_to_update = factories.UserFactory(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
        )
        self.group = Group.objects.create(name="Test Group")
        self.url = reverse("apps.users:user_update", args=[self.user_to_update.pk])

    def test_get_requires_login(self) -> None:
        """Test that view requires authentication."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_requires_permission(self) -> None:
        """Test that view requires change_user permission."""
        user_without_permission = factories.UserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_returns_200(self) -> None:
        """Test GET request returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/form.html")

    def test_post_updates_user(self) -> None:
        """Test POST request updates user."""
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "john.doe@example.com",
            "password": "",
            "confirm_password": "",
            "groups": [self.group.pk],
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("apps.users:user_list"))

        # Verify user was updated
        self.user_to_update.refresh_from_db()
        self.assertEqual(self.user_to_update.first_name, "Jane")
        self.assertEqual(self.user_to_update.last_name, "Smith")
        self.assertIn(self.group, self.user_to_update.groups.all())

    def test_post_updates_password(self) -> None:
        """Test POST request updates user password."""
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "john.doe@example.com",
            "password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!",
            "groups": [self.group.pk],
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        # Verify password was updated
        self.user_to_update.refresh_from_db()
        self.assertTrue(self.user_to_update.check_password("NewSecurePass123!"))

    def test_post_with_invalid_data(self) -> None:
        """Test POST with invalid data shows errors."""
        data = {
            "first_name": "",
            "last_name": "Smith",
            "email": "john.doe@example.com",
            "password": "",
            "confirm_password": "",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        # Just verify form is not valid
        self.assertFalse(response.context["form"].is_valid())


class UserDeleteViewTest(TestCase):
    """Test cases for UserDeleteView."""

    def setUp(self) -> None:
        """Set up test data."""
        self.admin = factories.StaffUserFactory()
        self.admin.is_superuser = False
        self.admin.save()
        self.client.force_login(self.admin)

        # Add delete_user permission
        permission = Permission.objects.get(codename="delete_user")
        self.admin.user_permissions.add(permission)

        self.user_to_delete = factories.UserFactory(email="delete@example.com")
        self.url = reverse("apps.users:user_delete", args=[self.user_to_delete.pk])

    def test_get_requires_login(self) -> None:
        """Test that view requires authentication."""
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_post_requires_permission(self) -> None:
        """Test that view requires delete_user permission."""
        user_without_permission = factories.UserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_post_deletes_user(self) -> None:
        """Test POST request deletes user."""
        user_pk = self.user_to_delete.pk

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("apps.users:user_list"))

        # Verify user was deleted
        self.assertFalse(User.objects.filter(pk=user_pk).exists())

    def test_cannot_delete_own_account(self) -> None:
        """Test that user cannot delete their own account."""
        url = reverse("apps.users:user_delete", args=[self.admin.pk])

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # Verify user still exists
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
