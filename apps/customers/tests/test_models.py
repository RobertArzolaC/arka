from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.customers import choices, factories, models


class CompanyModelTest(TestCase):
    """Test cases for the Company model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.company = factories.CompanyFactory()

    def test_company_creation(self) -> None:
        """Test that a company can be created successfully."""
        self.assertIsNotNone(self.company.pk)
        self.assertIsInstance(self.company, models.Company)

    def test_company_str_method(self) -> None:
        """Test the string representation of a company."""
        self.assertEqual(
            str(self.company),
            self.company.commercial_name or self.company.business_name,
        )

    def test_company_domain_unique(self) -> None:
        """Test that company domain must be unique."""
        with self.assertRaises(IntegrityError):
            factories.CompanyFactory(domain=self.company.domain)

    def test_company_ruc_unique(self) -> None:
        """Test that company RUC must be unique."""
        with self.assertRaises(IntegrityError):
            factories.CompanyFactory(ruc=self.company.ruc)

    def test_company_domain_validation(self) -> None:
        """Test that domain validation works correctly."""
        company = models.Company(
            domain="invalid domain!",
            regime=choices.TaxRegimeChoices.GENERAL,
            ruc="20123456789",
            business_name="Test Company",
            commercial_name="Test",
            address="Test Address",
        )
        with self.assertRaises(ValidationError):
            company.full_clean()

    def test_company_regime_choices(self) -> None:
        """Test that regime field has correct choices."""
        company = factories.CompanyFactory(regime=choices.TaxRegimeChoices.MYPE)
        self.assertEqual(company.regime, choices.TaxRegimeChoices.MYPE)

    def test_company_soft_delete(self) -> None:
        """Test that company can be soft deleted."""
        company_id = self.company.pk
        self.company.delete()

        # Refresh from DB to get the updated state
        self.company.refresh_from_db()

        # Should have is_removed set to timestamp
        self.assertIsNotNone(self.company.is_removed)

    def test_company_timestamps(self) -> None:
        """Test that created and modified timestamps are set."""
        self.assertIsNotNone(self.company.created)
        self.assertIsNotNone(self.company.modified)


class CompanyCredentialsModelTest(TestCase):
    """Test cases for the CompanyCredentials model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.company = factories.CompanyFactory()
        self.credentials = factories.CompanyCredentialsFactory(company=self.company)

    def test_credentials_creation(self) -> None:
        """Test that credentials can be created successfully."""
        self.assertIsNotNone(self.credentials.pk)
        self.assertEqual(self.credentials.company, self.company)

    def test_credentials_str_method(self) -> None:
        """Test the string representation of credentials."""
        expected = f"Credentials for {self.company.commercial_name}"
        self.assertEqual(str(self.credentials), expected)

    def test_credentials_one_to_one_relationship(self) -> None:
        """Test that a company can have only one credentials instance."""
        with self.assertRaises(IntegrityError):
            factories.CompanyCredentialsFactory(company=self.company)

    def test_credentials_remain_after_soft_delete(self) -> None:
        """Test that credentials remain when company is soft deleted."""
        credentials_id = self.credentials.pk
        self.company.delete()

        # Since Company uses soft delete, credentials should still exist
        self.assertTrue(
            models.CompanyCredentials.objects.filter(pk=credentials_id).exists()
        )


class CompanyAPICredentialsModelTest(TestCase):
    """Test cases for the CompanyAPICredentials model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.company = factories.CompanyFactory()
        self.api_credentials = factories.CompanyAPICredentialsFactory(
            company=self.company
        )

    def test_api_credentials_creation(self) -> None:
        """Test that API credentials can be created successfully."""
        self.assertIsNotNone(self.api_credentials.pk)
        self.assertEqual(self.api_credentials.company, self.company)

    def test_api_credentials_str_method(self) -> None:
        """Test the string representation of API credentials."""
        expected = f"API Credentials for {self.company.commercial_name}"
        self.assertEqual(str(self.api_credentials), expected)

    def test_api_credentials_one_to_one_relationship(self) -> None:
        """Test that a company can have only one API credentials instance."""
        with self.assertRaises(IntegrityError):
            factories.CompanyAPICredentialsFactory(company=self.company)

    def test_api_credentials_remain_after_soft_delete(self) -> None:
        """Test that API credentials remain when company is soft deleted."""
        api_credentials_id = self.api_credentials.pk
        self.company.delete()

        # Since Company uses soft delete, API credentials should still exist
        self.assertTrue(
            models.CompanyAPICredentials.objects.filter(
                pk=api_credentials_id
            ).exists()
        )


class CompanyCertificateModelTest(TestCase):
    """Test cases for the CompanyCertificate model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.company = factories.CompanyFactory()
        self.certificate = factories.CompanyCertificateFactory(company=self.company)

    def test_certificate_creation(self) -> None:
        """Test that certificate can be created successfully."""
        self.assertIsNotNone(self.certificate.pk)
        self.assertEqual(self.certificate.company, self.company)

    def test_certificate_str_method(self) -> None:
        """Test the string representation of certificate."""
        expected = f"Certificate for {self.company.commercial_name}"
        self.assertEqual(str(self.certificate), expected)

    def test_certificate_one_to_one_relationship(self) -> None:
        """Test that a company can have only one certificate instance."""
        with self.assertRaises(IntegrityError):
            factories.CompanyCertificateFactory(company=self.company)

    def test_certificate_remain_after_soft_delete(self) -> None:
        """Test that certificate remains when company is soft deleted."""
        certificate_id = self.certificate.pk
        self.company.delete()

        # Since Company uses soft delete, certificate should still exist
        self.assertTrue(
            models.CompanyCertificate.objects.filter(pk=certificate_id).exists()
        )

    def test_certificate_pen_field(self) -> None:
        """Test that certificate has PEN field for SUNAT."""
        self.assertIsNotNone(self.certificate.certificate_pen)
        self.assertIn("BEGIN CERTIFICATE", self.certificate.certificate_pen)
