"""Tests for Branch and DocumentSeries views."""

import json

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.customers import factories, models
from apps.users import factories as user_factories


class BranchViewsTest(TestCase):
    """Test cases for Branch views."""

    def setUp(self):
        """Set up test data and authenticate user."""
        self.user = user_factories.UserFactory()
        self.company = factories.CompanyFactory()

        # Add permissions to user
        permissions = Permission.objects.filter(
            codename__in=[
                "view_branch",
                "add_branch",
                "change_branch",
                "delete_branch",
            ]
        )
        self.user.user_permissions.add(*permissions)

        self.client.force_login(self.user)

    def test_branch_create_view_get(self):
        """Test accessing the branch create page."""
        url = reverse(
            "apps.customers:branch_create",
            kwargs={"company_pk": self.company.pk},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "customers/branch/form.html")
        self.assertIn("form", response.context)

    def test_branch_create_view_post_success(self):
        """Test creating a branch via POST."""
        url = reverse(
            "apps.customers:branch_create",
            kwargs={"company_pk": self.company.pk},
        )

        data = {
            "name": "Sucursal Lima",
            "description": "Main branch",
            "sunat_code": "0001",
            "address": "Av. Test 123",
            "phone": "987654321",
            "email": "lima@company.com",
        }

        response = self.client.post(url, data)

        # Check redirect
        self.assertEqual(response.status_code, 302)

        # Check branch was created
        branch = models.Branch.objects.get(
            company=self.company,
            sunat_code="0001",
        )
        self.assertEqual(branch.name, "Sucursal Lima")

    def test_branch_create_view_invalid_data(self):
        """Test creating a branch with invalid data."""
        url = reverse(
            "apps.customers:branch_create",
            kwargs={"company_pk": self.company.pk},
        )

        data = {
            "name": "Test Branch",
            "sunat_code": "ABC",  # Invalid: not 4 digits
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("sunat_code", response.context["form"].errors)

    def test_branch_update_view_get(self):
        """Test accessing the branch update page."""
        branch = factories.BranchFactory(company=self.company)

        url = reverse(
            "apps.customers:branch_update",
            kwargs={"company_pk": self.company.pk, "pk": branch.pk},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "customers/branch/update.html")
        self.assertIn("form", response.context)
        self.assertIn("document_series", response.context)
        self.assertIn("series_form", response.context)

    def test_branch_update_view_post_success(self):
        """Test updating a branch via POST."""
        branch = factories.BranchFactory(
            company=self.company,
            name="Old Name",
        )

        url = reverse(
            "apps.customers:branch_update",
            kwargs={"company_pk": self.company.pk, "pk": branch.pk},
        )

        data = {
            "name": "New Name",
            "description": "Updated description",
            "sunat_code": branch.sunat_code,
            "address": "New Address",
        }

        response = self.client.post(url, data)

        # Check redirect
        self.assertEqual(response.status_code, 302)

        # Check branch was updated
        branch.refresh_from_db()
        self.assertEqual(branch.name, "New Name")
        self.assertEqual(branch.address, "New Address")

    def test_branch_delete_view_ajax(self):
        """Test deleting a branch via AJAX."""
        branch = factories.BranchFactory(company=self.company)

        url = reverse(
            "apps.customers:branch_delete",
            kwargs={"company_pk": self.company.pk, "pk": branch.pk},
        )

        response = self.client.delete(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)

        # Check branch was soft deleted
        branch.refresh_from_db()
        self.assertTrue(branch.is_removed)


class DocumentSeriesViewsTest(TestCase):
    """Test cases for DocumentSeries views."""

    def setUp(self):
        """Set up test data and authenticate user."""
        self.user = user_factories.UserFactory()
        self.company = factories.CompanyFactory()
        self.branch = factories.BranchFactory(company=self.company)

        # Add permissions to user
        permissions = Permission.objects.filter(
            codename__in=[
                "add_documentseries",
                "delete_documentseries",
            ]
        )
        self.user.user_permissions.add(*permissions)

        self.client.force_login(self.user)

    def test_document_series_create_ajax_success(self):
        """Test creating a document series via AJAX."""
        url = reverse(
            "apps.customers:document_series_create",
            kwargs={"company_pk": self.company.pk, "branch_pk": self.branch.pk},
        )

        data = {
            "document_type": "01",  # Factura
            "series_number": "F001",
            "current_correlative": 1,
        }

        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("series", response_data)

        # Check series was created
        series = models.DocumentSeries.objects.get(
            branch=self.branch,
            document_type="01",
        )
        self.assertEqual(series.series_number, "F001")

    def test_document_series_create_ajax_invalid_data(self):
        """Test creating a document series with invalid data via AJAX."""
        url = reverse(
            "apps.customers:document_series_create",
            kwargs={"company_pk": self.company.pk, "branch_pk": self.branch.pk},
        )

        data = {
            "document_type": "01",  # Factura
            "series_number": "B001",  # Invalid: should start with F
            "current_correlative": 1,
        }

        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("errors", response_data)

    def test_document_series_create_duplicate_series(self):
        """Test creating a duplicate document series."""
        # Create first series
        factories.DocumentSeriesFactory(
            branch=self.branch,
            document_type="01",
            series_number="F001",
        )

        url = reverse(
            "apps.customers:document_series_create",
            kwargs={"company_pk": self.company.pk, "branch_pk": self.branch.pk},
        )

        data = {
            "document_type": "01",
            "series_number": "F001",
            "current_correlative": 1,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])

    def test_document_series_delete_ajax_success(self):
        """Test deleting a document series via AJAX."""
        series = factories.DocumentSeriesFactory(branch=self.branch)

        url = reverse(
            "apps.customers:document_series_delete",
            kwargs={
                "company_pk": self.company.pk,
                "branch_pk": self.branch.pk,
                "pk": series.pk,
            },
        )

        response = self.client.delete(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])

        # Check series was soft deleted
        series.refresh_from_db()
        self.assertTrue(series.is_removed)

    def test_document_series_delete_nonexistent(self):
        """Test deleting a non-existent document series."""
        url = reverse(
            "apps.customers:document_series_delete",
            kwargs={
                "company_pk": self.company.pk,
                "branch_pk": self.branch.pk,
                "pk": 99999,
            },
        )

        response = self.client.delete(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 404)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])

    def test_document_series_create_requires_permission(self):
        """Test that creating a series requires proper permissions."""
        # Create user without permissions
        user_no_perms = user_factories.UserFactory()
        self.client.force_login(user_no_perms)

        url = reverse(
            "apps.customers:document_series_create",
            kwargs={"company_pk": self.company.pk, "branch_pk": self.branch.pk},
        )

        data = {
            "document_type": "01",
            "series_number": "F001",
            "current_correlative": 1,
        }

        response = self.client.post(url, data)

        # Should be redirected to login or forbidden
        self.assertIn(response.status_code, [302, 403])

    def test_document_series_delete_requires_permission(self):
        """Test that deleting a series requires proper permissions."""
        series = factories.DocumentSeriesFactory(branch=self.branch)

        # Create user without permissions
        user_no_perms = user_factories.UserFactory()
        self.client.force_login(user_no_perms)

        url = reverse(
            "apps.customers:document_series_delete",
            kwargs={
                "company_pk": self.company.pk,
                "branch_pk": self.branch.pk,
                "pk": series.pk,
            },
        )

        response = self.client.delete(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Should be redirected to login or forbidden
        self.assertIn(response.status_code, [302, 403])
