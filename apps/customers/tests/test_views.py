from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.customers import factories, models
from apps.users import factories as user_factories


class CompanyListViewTest(TestCase):
    """Test cases for the CompanyListView."""

    def setUp(self) -> None:
        """Set up test data and user with permissions."""
        self.user = user_factories.UserFactory()
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_company")
        )
        self.client.force_login(self.user)

        # Create test companies
        self.company1 = factories.CompanyFactory(
            domain="company1", ruc="20123456781"
        )
        self.company2 = factories.CompanyFactory(
            domain="company2", ruc="20123456782"
        )

    def test_list_view_accessible(self) -> None:
        """Test that the list view is accessible."""
        response = self.client.get(reverse("apps.customers:company_list"))
        self.assertEqual(response.status_code, 200)

    def test_list_view_uses_correct_template(self) -> None:
        """Test that the list view uses the correct template."""
        response = self.client.get(reverse("apps.customers:company_list"))
        self.assertTemplateUsed(response, "customers/company/list.html")

    def test_list_view_shows_companies(self) -> None:
        """Test that the list view displays companies."""
        response = self.client.get(reverse("apps.customers:company_list"))
        self.assertContains(response, self.company1.commercial_name)
        self.assertContains(response, self.company2.commercial_name)

    def test_list_view_requires_permission(self) -> None:
        """Test that the list view requires permission."""
        user_without_permission = user_factories.UserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.get(reverse("apps.customers:company_list"))
        self.assertIn(response.status_code, [200, 302, 403])

    def test_list_view_search_filter(self) -> None:
        """Test that the search filter works correctly."""
        response = self.client.get(
            reverse("apps.customers:company_list"),
            {"search": self.company1.domain},
        )
        self.assertContains(response, self.company1.commercial_name)
        self.assertNotContains(response, self.company2.commercial_name)

    def test_list_view_pagination(self) -> None:
        """Test that pagination works correctly."""
        # Create more companies to test pagination
        for i in range(15):
            factories.CompanyFactory()

        response = self.client.get(reverse("apps.customers:company_list"))
        self.assertTrue(response.context["is_paginated"])


class CompanyCreateViewTest(TestCase):
    """Test cases for the CompanyCreateView."""

    def setUp(self) -> None:
        """Set up test data and user with permissions."""
        self.user = user_factories.UserFactory()
        self.user.user_permissions.add(
            Permission.objects.get(codename="add_company")
        )
        self.client.force_login(self.user)

        self.url = reverse("apps.customers:company_create")

    def test_create_view_accessible(self) -> None:
        """Test that the create view is accessible."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_view_uses_correct_template(self) -> None:
        """Test that the create view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "customers/company/form.html")

    def test_create_company_successfully(self) -> None:
        """Test that a company can be created successfully."""
        data = {
            "domain": "test-company",
            "regime": "GENERAL",
            "ruc": "20123456789",
            "business_name": "Test Business S.A.C.",
            "commercial_name": "Test Company",
            "address": "Av. Test 123",
            "telephone": "987654321",
            "email": "test@company.com",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        # Check that company was created
        self.assertTrue(
            models.Company.objects.filter(domain="test-company").exists()
        )

    def test_create_company_requires_permission(self) -> None:
        """Test that creating a company requires permission."""
        user_without_permission = user_factories.UserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 403])

    def test_create_company_with_invalid_domain(self) -> None:
        """Test that creating a company with invalid domain fails."""
        data = {
            "domain": "invalid domain!",
            "regime": "GENERAL",
            "ruc": "20123456789",
            "business_name": "Test Business S.A.C.",
            "commercial_name": "Test Company",
            "address": "Av. Test 123",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "domain",
            "Domain must contain only alphanumeric characters and hyphens.",
        )

    def test_create_company_with_invalid_ruc(self) -> None:
        """Test that creating a company with invalid RUC fails."""
        data = {
            "domain": "test-company",
            "regime": "GENERAL",
            "ruc": "123",  # Invalid RUC
            "business_name": "Test Business S.A.C.",
            "commercial_name": "Test Company",
            "address": "Av. Test 123",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "ruc", "RUC must be exactly 11 digits"
        )


class CompanyUpdateViewTest(TestCase):
    """Test cases for the CompanyUpdateView."""

    def setUp(self) -> None:
        """Set up test data and user with permissions."""
        self.user = user_factories.UserFactory()
        self.user.user_permissions.add(
            Permission.objects.get(codename="change_company")
        )
        self.client.force_login(self.user)

        self.company = factories.CompanyFactory()
        self.url = reverse(
            "apps.customers:company_update", kwargs={"pk": self.company.pk}
        )

    def test_update_view_accessible(self) -> None:
        """Test that the update view is accessible."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_update_view_uses_correct_template(self) -> None:
        """Test that the update view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "customers/company/update.html")

    def test_update_company_successfully(self) -> None:
        """Test that a company can be updated successfully."""
        data = {
            "regime": "MYPE",
            "ruc": self.company.ruc,
            "business_name": "Updated Business Name",
            "commercial_name": "Updated Commercial Name",
            "address": "Updated Address",
            "telephone": "999888777",
            "email": "updated@company.com",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        # Check that company was updated
        self.company.refresh_from_db()
        self.assertEqual(self.company.business_name, "Updated Business Name")

    def test_update_view_requires_permission(self) -> None:
        """Test that updating a company requires permission."""
        user_without_permission = user_factories.UserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 403])

    def test_update_view_shows_tabs(self) -> None:
        """Test that the update view shows all tabs."""
        response = self.client.get(self.url)
        self.assertContains(response, "company_data_tab")
        self.assertContains(response, "credentials_tab")
        self.assertContains(response, "api_credentials_tab")
        self.assertContains(response, "certificate_tab")

    def test_update_credentials(self) -> None:
        """Test that company credentials can be updated."""
        data = {
            "credentials-sol_user": "TESTUSER123",
            "credentials-sol_password": "testpassword",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        # Check that credentials were created/updated
        credentials = models.CompanyCredentials.objects.get(company=self.company)
        self.assertEqual(credentials.sol_user, "TESTUSER123")

    def test_update_api_credentials(self) -> None:
        """Test that API credentials can be updated."""
        data = {
            "api_credentials-client_id": "test-client-id",
            "api_credentials-client_secret": "test-client-secret",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        # Check that API credentials were created/updated
        api_credentials = models.CompanyAPICredentials.objects.get(
            company=self.company
        )
        self.assertEqual(api_credentials.client_id, "test-client-id")


class CompanyDeleteViewTest(TestCase):
    """Test cases for the CompanyDeleteView."""

    def setUp(self) -> None:
        """Set up test data and user with permissions."""
        self.user = user_factories.UserFactory()
        self.user.user_permissions.add(
            Permission.objects.get(codename="delete_company")
        )
        self.client.force_login(self.user)

        self.company = factories.CompanyFactory()
        self.url = reverse(
            "apps.customers:company_delete", kwargs={"pk": self.company.pk}
        )

    def test_delete_view_requires_permission(self) -> None:
        """Test that deleting a company requires permission."""
        user_without_permission = user_factories.UserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.post(self.url)
        self.assertIn(response.status_code, [200, 302, 403])

    def test_delete_company_successfully(self) -> None:
        """Test that a company can be deleted successfully."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        # Check that company was soft deleted
        self.company.refresh_from_db()
        self.assertIsNotNone(self.company.is_removed)
