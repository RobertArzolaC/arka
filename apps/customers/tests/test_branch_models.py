"""Tests for Branch and DocumentSeries models."""

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.customers import factories, models


class BranchModelTest(TestCase):
    """Test cases for the Branch model."""

    def setUp(self):
        """Set up test data."""
        self.company = factories.CompanyFactory()

    def test_branch_creation(self):
        """Test creating a branch successfully."""
        branch = factories.BranchFactory(
            company=self.company,
            name="Sucursal Lima",
            sunat_code="0001",
        )

        self.assertEqual(branch.name, "Sucursal Lima")
        self.assertEqual(branch.sunat_code, "0001")
        self.assertEqual(branch.company, self.company)

    def test_branch_str_representation(self):
        """Test the string representation of a branch."""
        # Get the automatically created Principal branch
        branch = models.Branch.objects.get(
            company=self.company,
            sunat_code="0000",
        )

        expected = f"Principal (0000) - {self.company.commercial_name}"
        self.assertEqual(str(branch), expected)

    def test_branch_unique_sunat_code_per_company(self):
        """Test that SUNAT code must be unique per company."""
        factories.BranchFactory(
            company=self.company,
            sunat_code="0001",
        )

        with self.assertRaises(IntegrityError):
            factories.BranchFactory(
                company=self.company,
                sunat_code="0001",
            )

    def test_branch_same_sunat_code_different_companies(self):
        """Test that same SUNAT code can exist for different companies."""
        company2 = factories.CompanyFactory()

        branch1 = factories.BranchFactory(
            company=self.company,
            sunat_code="0001",
        )
        branch2 = factories.BranchFactory(
            company=company2,
            sunat_code="0001",
        )

        self.assertEqual(branch1.sunat_code, branch2.sunat_code)
        self.assertNotEqual(branch1.company, branch2.company)

    def test_company_creates_principal_branch_on_save(self):
        """Test that creating a company automatically creates a Principal branch."""
        new_company = factories.CompanyFactory()

        # Check that a branch was created
        branches = models.Branch.objects.filter(company=new_company)
        self.assertEqual(branches.count(), 1)

        # Check that it's the Principal branch
        principal_branch = branches.first()
        self.assertEqual(principal_branch.name, "Principal")
        self.assertEqual(principal_branch.sunat_code, "0000")

    def test_branch_inherits_company_address(self):
        """Test that Principal branch inherits company address data."""
        new_company = factories.CompanyFactory(
            address="Av. Test 123",
            phone="123456789",
            email="test@company.com",
        )

        principal_branch = models.Branch.objects.get(
            company=new_company,
            sunat_code="0000",
        )

        self.assertEqual(principal_branch.address, new_company.address)
        self.assertEqual(principal_branch.phone, new_company.phone)
        self.assertEqual(principal_branch.email, new_company.email)


class DocumentSeriesModelTest(TestCase):
    """Test cases for the DocumentSeries model."""

    def setUp(self):
        """Set up test data."""
        self.company = factories.CompanyFactory()
        self.branch = factories.BranchFactory(company=self.company)

    def test_document_series_creation(self):
        """Test creating a document series successfully."""
        series = factories.DocumentSeriesFactory(
            branch=self.branch,
            document_type="01",  # Factura
            series_number="F001",
            current_correlative=1,
        )

        self.assertEqual(series.document_type, "01")
        self.assertEqual(series.series_number, "F001")
        self.assertEqual(series.current_correlative, 1)
        self.assertEqual(series.branch, self.branch)

    def test_document_series_str_representation(self):
        """Test the string representation of a document series."""
        series = factories.DocumentSeriesFactory(
            branch=self.branch,
            document_type="01",
            series_number="F001",
        )

        expected = f"Factura Electrónica - F001 ({self.branch.name})"
        self.assertEqual(str(series), expected)

    def test_document_series_unique_per_branch(self):
        """Test that series must be unique per branch and document type."""
        factories.DocumentSeriesFactory(
            branch=self.branch,
            document_type="01",
            series_number="F001",
        )

        with self.assertRaises(IntegrityError):
            factories.DocumentSeriesFactory(
                branch=self.branch,
                document_type="01",
                series_number="F001",
            )

    def test_document_series_same_series_different_branches(self):
        """Test that same series can exist for different branches."""
        branch2 = factories.BranchFactory(company=self.company)

        series1 = factories.DocumentSeriesFactory(
            branch=self.branch,
            document_type="01",
            series_number="F001",
        )
        series2 = factories.DocumentSeriesFactory(
            branch=branch2,
            document_type="01",
            series_number="F001",
        )

        self.assertEqual(series1.series_number, series2.series_number)
        self.assertNotEqual(series1.branch, series2.branch)

    def test_get_next_correlative(self):
        """Test getting the next correlative number."""
        series = factories.DocumentSeriesFactory(
            branch=self.branch,
            document_type="01",
            series_number="F001",
            current_correlative=5,
        )

        correlative = series.get_next_correlative()

        self.assertEqual(correlative, "00000005")
        series.refresh_from_db()
        self.assertEqual(series.current_correlative, 6)

    def test_get_next_correlative_increments(self):
        """Test that get_next_correlative increments each time."""
        series = factories.DocumentSeriesFactory(
            branch=self.branch,
            document_type="01",
            series_number="F001",
            current_correlative=1,
        )

        correlative1 = series.get_next_correlative()
        correlative2 = series.get_next_correlative()
        correlative3 = series.get_next_correlative()

        self.assertEqual(correlative1, "00000001")
        self.assertEqual(correlative2, "00000002")
        self.assertEqual(correlative3, "00000003")

        series.refresh_from_db()
        self.assertEqual(series.current_correlative, 4)

    def test_correlative_format_with_leading_zeros(self):
        """Test that correlative is formatted with 8 digits and leading zeros."""
        series = factories.DocumentSeriesFactory(
            branch=self.branch,
            current_correlative=42,
        )

        correlative = series.get_next_correlative()
        self.assertEqual(correlative, "00000042")
        self.assertEqual(len(correlative), 8)
