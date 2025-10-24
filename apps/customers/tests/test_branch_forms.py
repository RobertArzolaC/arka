"""Tests for Branch and DocumentSeries forms."""

from django.test import TestCase

from apps.customers import factories, forms


class BranchFormTest(TestCase):
    """Test cases for the BranchForm."""

    def test_branch_form_valid_data(self):
        """Test form with valid data."""
        form_data = {
            "name": "Sucursal Lima",
            "description": "Main branch in Lima",
            "sunat_code": "0001",
            "address": "Av. Test 123",
            "phone": "987654321",
            "email": "lima@company.com",
            "website": "https://company.com",
        }

        form = forms.BranchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_branch_form_missing_required_fields(self):
        """Test form with missing required fields."""
        form_data = {
            "description": "Test branch",
        }

        form = forms.BranchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("sunat_code", form.errors)

    def test_branch_form_invalid_sunat_code_non_digits(self):
        """Test form with non-digit SUNAT code."""
        form_data = {
            "name": "Test Branch",
            "sunat_code": "ABC1",
            "address": "Test Address",
        }

        form = forms.BranchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("sunat_code", form.errors)

    def test_branch_form_invalid_sunat_code_length(self):
        """Test form with invalid SUNAT code length."""
        form_data = {
            "name": "Test Branch",
            "sunat_code": "001",  # Only 3 digits
            "address": "Test Address",
        }

        form = forms.BranchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("sunat_code", form.errors)

    def test_branch_form_valid_sunat_code(self):
        """Test form with valid 4-digit SUNAT code."""
        form_data = {
            "name": "Test Branch",
            "sunat_code": "0001",
            "address": "Test Address",
        }

        form = forms.BranchForm(data=form_data)
        self.assertTrue(form.is_valid())


class DocumentSeriesFormTest(TestCase):
    """Test cases for the DocumentSeriesForm."""

    def test_document_series_form_valid_factura(self):
        """Test form with valid Factura series."""
        form_data = {
            "document_type": "01",  # Factura
            "series_number": "F001",
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_document_series_form_valid_boleta(self):
        """Test form with valid Boleta series."""
        form_data = {
            "document_type": "03",  # Boleta
            "series_number": "B001",
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_document_series_form_valid_guia_remision(self):
        """Test form with valid Guía de Remisión series."""
        form_data = {
            "document_type": "09",  # Guía de Remisión
            "series_number": "T001",
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_document_series_form_invalid_factura_prefix(self):
        """Test form with invalid Factura series prefix."""
        form_data = {
            "document_type": "01",  # Factura
            "series_number": "B001",  # Should start with F
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_document_series_form_invalid_boleta_prefix(self):
        """Test form with invalid Boleta series prefix."""
        form_data = {
            "document_type": "03",  # Boleta
            "series_number": "F001",  # Should start with B
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_document_series_form_invalid_guia_prefix(self):
        """Test form with invalid Guía series prefix."""
        form_data = {
            "document_type": "09",  # Guía de Remisión
            "series_number": "F001",  # Should start with T
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_document_series_form_nota_credito_accepts_f_or_b(self):
        """Test that Nota de Crédito accepts both F and B prefixes."""
        # Test with F prefix
        form_data_f = {
            "document_type": "07",  # Nota de Crédito
            "series_number": "F001",
            "current_correlative": 1,
        }
        form_f = forms.DocumentSeriesForm(data=form_data_f)
        self.assertTrue(form_f.is_valid())

        # Test with B prefix
        form_data_b = {
            "document_type": "07",  # Nota de Crédito
            "series_number": "B001",
            "current_correlative": 1,
        }
        form_b = forms.DocumentSeriesForm(data=form_data_b)
        self.assertTrue(form_b.is_valid())

    def test_document_series_form_nota_debito_accepts_f_or_b(self):
        """Test that Nota de Débito accepts both F and B prefixes."""
        # Test with F prefix
        form_data_f = {
            "document_type": "08",  # Nota de Débito
            "series_number": "F001",
            "current_correlative": 1,
        }
        form_f = forms.DocumentSeriesForm(data=form_data_f)
        self.assertTrue(form_f.is_valid())

        # Test with B prefix
        form_data_b = {
            "document_type": "08",  # Nota de Débito
            "series_number": "B001",
            "current_correlative": 1,
        }
        form_b = forms.DocumentSeriesForm(data=form_data_b)
        self.assertTrue(form_b.is_valid())

    def test_document_series_form_invalid_series_length(self):
        """Test form with invalid series number length."""
        form_data = {
            "document_type": "01",  # Factura
            "series_number": "F01",  # Only 3 characters
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_document_series_form_invalid_series_format(self):
        """Test form with invalid series format (not letter + 3 digits)."""
        form_data = {
            "document_type": "01",  # Factura
            "series_number": "FA01",  # Two letters instead of one
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_document_series_form_uppercase_conversion(self):
        """Test that series number is converted to uppercase."""
        form_data = {
            "document_type": "01",  # Factura
            "series_number": "f001",  # Lowercase
            "current_correlative": 1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["series_number"], "F001")

    def test_document_series_form_missing_required_fields(self):
        """Test form with missing required fields."""
        form_data = {}

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("document_type", form.errors)
        self.assertIn("series_number", form.errors)
        self.assertIn("current_correlative", form.errors)

    def test_document_series_form_negative_correlative(self):
        """Test form with negative correlative value."""
        form_data = {
            "document_type": "01",
            "series_number": "F001",
            "current_correlative": -1,
        }

        form = forms.DocumentSeriesForm(data=form_data)
        self.assertFalse(form.is_valid())
