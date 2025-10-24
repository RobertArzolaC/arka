from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.customers import choices, factories, forms, models


class CompanyFormTest(TestCase):
    """Test cases for the CompanyForm."""

    def test_form_valid_data(self) -> None:
        """Test that form is valid with correct data."""
        data = {
            "domain": "test-company",
            "regime": choices.TaxRegimeChoices.GENERAL,
            "ruc": "20123456789",
            "business_name": "Test Business S.A.C.",
            "commercial_name": "Test Company",
            "address": "Av. Test 123",
            "telephone": "987654321",
            "email": "test@company.com",
        }

        form = forms.CompanyForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_ruc_non_digit(self) -> None:
        """Test that form is invalid with non-digit RUC."""
        data = {
            "domain": "test-company",
            "regime": choices.TaxRegimeChoices.GENERAL,
            "ruc": "2012345678A",
            "business_name": "Test Business S.A.C.",
            "commercial_name": "Test Company",
            "address": "Av. Test 123",
        }

        form = forms.CompanyForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("ruc", form.errors)
        self.assertIn("RUC must contain only digits", str(form.errors["ruc"]))

    def test_form_invalid_ruc_length(self) -> None:
        """Test that form is invalid with incorrect RUC length."""
        data = {
            "domain": "test-company",
            "regime": choices.TaxRegimeChoices.GENERAL,
            "ruc": "123456789",  # Only 9 digits
            "business_name": "Test Business S.A.C.",
            "commercial_name": "Test Company",
            "address": "Av. Test 123",
        }

        form = forms.CompanyForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("ruc", form.errors)
        self.assertIn("RUC must be exactly 11 digits", str(form.errors["ruc"]))

    def test_form_domain_lowercase_conversion(self) -> None:
        """Test that domain is converted to lowercase."""
        data = {
            "domain": "TEST-COMPANY",
            "regime": choices.TaxRegimeChoices.GENERAL,
            "ruc": "20123456789",
            "business_name": "Test Business S.A.C.",
            "commercial_name": "Test Company",
            "address": "Av. Test 123",
        }

        form = forms.CompanyForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["domain"], "test-company")

    def test_form_required_fields(self) -> None:
        """Test that required fields are enforced."""
        form = forms.CompanyForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("domain", form.errors)
        self.assertIn("regime", form.errors)
        self.assertIn("ruc", form.errors)
        self.assertIn("business_name", form.errors)
        self.assertIn("commercial_name", form.errors)
        # address is not required (comes from BaseAddress with blank=True)


class CompanyUpdateFormTest(TestCase):
    """Test cases for the CompanyUpdateForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.company = factories.CompanyFactory()

    def test_form_valid_data(self) -> None:
        """Test that form is valid with correct data."""
        data = {
            "regime": choices.TaxRegimeChoices.MYPE,
            "ruc": "20987654321",
            "business_name": "Updated Business",
            "commercial_name": "Updated Commercial",
            "address": "Updated Address",
            "telephone": "999888777",
            "email": "updated@company.com",
        }

        form = forms.CompanyUpdateForm(data=data, instance=self.company)
        self.assertTrue(form.is_valid())

    def test_form_includes_logo_fields(self) -> None:
        """Test that form includes logo upload fields."""
        form = forms.CompanyUpdateForm(instance=self.company)
        self.assertIn("square_logo", form.fields)
        self.assertIn("rectangular_logo", form.fields)


class CompanyCredentialsFormTest(TestCase):
    """Test cases for the CompanyCredentialsForm."""

    def test_form_valid_data(self) -> None:
        """Test that form is valid with correct data."""
        data = {
            "sol_user": "TESTUSER123",
            "sol_password": "testpassword",
        }

        form = forms.CompanyCredentialsForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_required_fields(self) -> None:
        """Test that required fields are enforced."""
        form = forms.CompanyCredentialsForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("sol_user", form.errors)
        self.assertIn("sol_password", form.errors)

    def test_form_password_widget(self) -> None:
        """Test that password field uses PasswordInput widget."""
        form = forms.CompanyCredentialsForm()
        self.assertEqual(
            form.fields["sol_password"].widget.__class__.__name__, "PasswordInput"
        )


class CompanyAPICredentialsFormTest(TestCase):
    """Test cases for the CompanyAPICredentialsForm."""

    def test_form_valid_data(self) -> None:
        """Test that form is valid with correct data."""
        data = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
        }

        form = forms.CompanyAPICredentialsForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_required_fields(self) -> None:
        """Test that required fields are enforced."""
        form = forms.CompanyAPICredentialsForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("client_id", form.errors)
        self.assertIn("client_secret", form.errors)

    def test_form_secret_widget(self) -> None:
        """Test that client_secret field uses PasswordInput widget."""
        form = forms.CompanyAPICredentialsForm()
        self.assertEqual(
            form.fields["client_secret"].widget.__class__.__name__, "PasswordInput"
        )


class CompanyCertificateFormTest(TestCase):
    """Test cases for the CompanyCertificateForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.company = factories.CompanyFactory()

    def test_form_valid_data(self) -> None:
        """Test that form is valid with correct data."""
        certificate_file = SimpleUploadedFile(
            "certificate.pfx", b"mock certificate content"
        )

        data = {"certificate_password": "certpassword"}
        files = {"certificate_file": certificate_file}

        form = forms.CompanyCertificateForm(data=data, files=files)
        self.assertTrue(form.is_valid())

    def test_form_save_generates_pen(self) -> None:
        """Test that saving form generates PEN certificate."""
        certificate_file = SimpleUploadedFile(
            "certificate.pfx", b"mock certificate content"
        )

        data = {"certificate_password": "certpassword"}
        files = {"certificate_file": certificate_file}

        certificate_instance = models.CompanyCertificate(company=self.company)
        form = forms.CompanyCertificateForm(
            data=data, files=files, instance=certificate_instance
        )

        self.assertTrue(form.is_valid())
        certificate = form.save()

        # Check that PEN was generated (mocked)
        self.assertIsNotNone(certificate.certificate_pen)
        self.assertIn("BEGIN CERTIFICATE", certificate.certificate_pen)

    def test_form_required_fields(self) -> None:
        """Test that required fields are enforced."""
        form = forms.CompanyCertificateForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("certificate_file", form.errors)
        self.assertIn("certificate_password", form.errors)

    def test_form_file_accept_attribute(self) -> None:
        """Test that file input has correct accept attribute."""
        form = forms.CompanyCertificateForm()
        widget_attrs = form.fields["certificate_file"].widget.attrs
        self.assertEqual(widget_attrs.get("accept"), ".pfx,.p12")
