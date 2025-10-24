"""Tests for user filters."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from apps.users import factories, filters

User = get_user_model()


class UserFilterTest(TestCase):
    """Test cases for UserFilter."""

    def setUp(self) -> None:
        """Set up test data."""
        self.group1 = Group.objects.create(name="Group 1")
        self.group2 = Group.objects.create(name="Group 2")

        self.user1 = factories.UserFactory(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            is_active=True,
            is_staff=False,
        )
        self.user1.groups.add(self.group1)

        self.user2 = factories.UserFactory(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            is_active=False,
            is_staff=True,
        )
        self.user2.groups.add(self.group2)

    def test_filter_by_name_first_name(self) -> None:
        """Test filtering by first name."""
        filterset = filters.UserFilter(
            data={"name_search": "John"},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user1, filterset.qs)
        self.assertNotIn(self.user2, filterset.qs)

    def test_filter_by_name_last_name(self) -> None:
        """Test filtering by last name."""
        filterset = filters.UserFilter(
            data={"name_search": "Smith"},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user2, filterset.qs)
        self.assertNotIn(self.user1, filterset.qs)

    def test_filter_by_name_email(self) -> None:
        """Test filtering by email."""
        filterset = filters.UserFilter(
            data={"name_search": "john@"},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user1, filterset.qs)
        self.assertNotIn(self.user2, filterset.qs)

    def test_filter_by_name_case_insensitive(self) -> None:
        """Test filtering by name is case insensitive."""
        filterset = filters.UserFilter(
            data={"name_search": "JOHN"},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user1, filterset.qs)

    def test_filter_by_active_status_true(self) -> None:
        """Test filtering by active status (active users)."""
        filterset = filters.UserFilter(
            data={"is_active": "true"},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user1, filterset.qs)
        self.assertNotIn(self.user2, filterset.qs)

    def test_filter_by_active_status_false(self) -> None:
        """Test filtering by active status (inactive users)."""
        filterset = filters.UserFilter(
            data={"is_active": "false"},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user2, filterset.qs)
        self.assertNotIn(self.user1, filterset.qs)

    def test_filter_by_group(self) -> None:
        """Test filtering by group."""
        filterset = filters.UserFilter(
            data={"groups": self.group1.pk},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user1, filterset.qs)
        self.assertNotIn(self.user2, filterset.qs)

    def test_filter_by_staff_status_true(self) -> None:
        """Test filtering by staff status (staff only)."""
        filterset = filters.UserFilter(
            data={"is_staff": "true"},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user2, filterset.qs)
        self.assertNotIn(self.user1, filterset.qs)

    def test_filter_by_staff_status_false(self) -> None:
        """Test filtering by staff status (non-staff only)."""
        filterset = filters.UserFilter(
            data={"is_staff": "false"},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user1, filterset.qs)
        self.assertNotIn(self.user2, filterset.qs)

    def test_multiple_filters(self) -> None:
        """Test applying multiple filters simultaneously."""
        filterset = filters.UserFilter(
            data={
                "name_search": "Jane",
                "is_active": "false",
                "is_staff": "true",
            },
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertIn(self.user2, filterset.qs)
        self.assertNotIn(self.user1, filterset.qs)

    def test_no_filters_returns_all(self) -> None:
        """Test that no filters returns all users."""
        filterset = filters.UserFilter(
            data={},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertEqual(filterset.qs.count(), User.objects.count())

    def test_empty_name_search_returns_all(self) -> None:
        """Test that empty name search returns all users."""
        filterset = filters.UserFilter(
            data={"name_search": ""},
            queryset=User.objects.all(),
        )
        self.assertTrue(filterset.is_valid())
        self.assertEqual(filterset.qs.count(), User.objects.count())
