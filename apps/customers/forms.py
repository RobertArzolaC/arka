from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from cities_light.models import Country
from constance import config
from dal import autocomplete
from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.customers import mixins, models
from apps.users import models as user_models


class AccountCreationForm(mixins.PermissionFormMixin, SignupForm):
    first_name = forms.CharField(max_length=30, label="First name")
    last_name = forms.CharField(max_length=30, label="Last name")
    avatar = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("password1", None)
        self.fields.pop("password2", None)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")

        if user_models.User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _("An account with this email already exists")
            )

        return cleaned_data

    def save(self, request):
        with transaction.atomic():
            user = super(AccountCreationForm, self).save(request)

            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.user_type = self.cleaned_data["user_type"]
            user.avatar = self.cleaned_data["avatar"]
            user.must_change_password = True

            temp_password = user_models.User.objects.make_random_password()
            user.set_password(temp_password)
            user.save()
            self.save_permissions(user)

            EmailAddress.objects.get_or_create(
                user=user, email=user.email, primary=True, verified=False
            )

            if config.ENABLE_SEND_EMAIL:
                send_email_confirmation(request, user, signup=True)

            return user


class AccountUpdateForm(mixins.PermissionFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=30, label=_("First name"))
    last_name = forms.CharField(max_length=30, label=_("Last name"))
    email = forms.EmailField(max_length=254, label=_("Email"), disabled=True)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = models.Account
        fields = ["avatar"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email
            self.fields["avatar"].initial = self.instance.user.avatar

    def save(self, commit=True):
        account = super().save(commit=False)
        user = account.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.avatar = self.cleaned_data.get("avatar")

        user.save()
        account.save()
        self.save_permissions(user)

        return account


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = models.Account
        fields = "__all__"


class CompanyForm(forms.ModelForm):
    """Form for creating and editing company basic information."""

    class Meta:
        model = models.Company
        fields = [
            "domain",
            "regime",
            "ruc",
            "business_name",
            "commercial_name",
            "address",
            "country",
            "region",
            "subregion",
            "city",
            "phone",
            "email",
        ]
        widgets = {
            "domain": forms.TextInput(attrs={"class": "form-control"}),
            "regime": forms.Select(attrs={"class": "form-select"}),
            "ruc": forms.TextInput(attrs={"class": "form-control"}),
            "business_name": forms.TextInput(attrs={"class": "form-control"}),
            "commercial_name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "country": autocomplete.ModelSelect2(
                url="apps.core:country-autocomplete",
                attrs={"class": "form-select", "data-control": "select2"},
            ),
            "region": autocomplete.ModelSelect2(
                url="apps.core:region-autocomplete",
                forward=["country"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Department"),
                },
            ),
            "subregion": autocomplete.ModelSelect2(
                url="apps.core:subregion-autocomplete",
                forward=["region"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Province"),
                },
            ),
            "city": autocomplete.ModelSelect2(
                url="apps.core:city-autocomplete",
                forward=["country", "region", "subregion"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("District"),
                },
            ),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with Peru as default country."""
        super().__init__(*args, **kwargs)

        # Set Peru as default country if creating a new company
        if not self.instance.pk:
            try:
                peru = Country.objects.get(slug="peru")
                self.initial["country"] = peru.pk
            except Country.DoesNotExist:
                pass

    def clean_ruc(self) -> str:
        """Validate RUC format (11 digits for Peru)."""
        ruc = self.cleaned_data.get("ruc")
        if ruc and not ruc.isdigit():
            raise forms.ValidationError(_("RUC must contain only digits"))
        if ruc and len(ruc) != 11:
            raise forms.ValidationError(_("RUC must be exactly 11 digits"))
        return ruc

    def clean_domain(self) -> str:
        """Ensure domain is lowercase and valid."""
        domain = self.cleaned_data.get("domain")
        if domain:
            domain = domain.lower()
        return domain


class CompanyUpdateForm(forms.ModelForm):
    """Form for updating company data including logos."""

    class Meta:
        model = models.Company
        fields = [
            "regime",
            "ruc",
            "business_name",
            "commercial_name",
            "address",
            "country",
            "region",
            "subregion",
            "city",
            "phone",
            "email",
            "square_logo",
            "rectangular_logo",
        ]
        widgets = {
            "regime": forms.Select(attrs={"class": "form-select"}),
            "ruc": forms.TextInput(attrs={"class": "form-control"}),
            "business_name": forms.TextInput(attrs={"class": "form-control"}),
            "commercial_name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "country": autocomplete.ModelSelect2(
                url="apps.core:country-autocomplete",
                attrs={"class": "form-select", "data-control": "select2"},
            ),
            "region": autocomplete.ModelSelect2(
                url="apps.core:region-autocomplete",
                forward=["country"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Department"),
                },
            ),
            "subregion": autocomplete.ModelSelect2(
                url="apps.core:subregion-autocomplete",
                forward=["region"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Province"),
                },
            ),
            "city": autocomplete.ModelSelect2(
                url="apps.core:city-autocomplete",
                forward=["country", "region", "subregion"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("District"),
                },
            ),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "square_logo": forms.FileInput(attrs={"class": "form-control"}),
            "rectangular_logo": forms.FileInput(
                attrs={"class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with Peru as default country if not set."""
        super().__init__(*args, **kwargs)

        # Set Peru as default country if company doesn't have one
        if self.instance and not self.instance.country_id:
            try:
                peru = Country.objects.get(slug="peru")
                self.initial["country"] = peru.pk
            except Country.DoesNotExist:
                pass


class CompanyCredentialsForm(forms.ModelForm):
    """Form for managing SUNAT credentials."""

    class Meta:
        model = models.CompanyCredentials
        fields = ["sol_user", "sol_password"]
        widgets = {
            "sol_user": forms.TextInput(attrs={"class": "form-control"}),
            "sol_password": forms.PasswordInput(
                attrs={"class": "form-control"}
            ),
        }


class CompanyAPICredentialsForm(forms.ModelForm):
    """Form for managing API credentials."""

    class Meta:
        model = models.CompanyAPICredentials
        fields = ["client_id", "client_secret"]
        widgets = {
            "client_id": forms.TextInput(attrs={"class": "form-control"}),
            "client_secret": forms.PasswordInput(
                attrs={"class": "form-control"}
            ),
        }


class CompanyCertificateForm(forms.ModelForm):
    """Form for uploading and managing digital certificates."""

    class Meta:
        model = models.CompanyCertificate
        fields = ["certificate_file", "certificate_password"]
        widgets = {
            "certificate_file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pfx,.p12",
                }
            ),
            "certificate_password": forms.PasswordInput(
                attrs={"class": "form-control"}
            ),
        }

    def save(self, commit: bool = True) -> models.CompanyCertificate:
        """Save certificate and simulate PEN conversion."""
        certificate = super().save(commit=False)

        # Simulate PEN conversion (placeholder)
        # In production, this would use OpenSSL to convert PFX to PEM
        certificate.certificate_pen = (
            "-----BEGIN CERTIFICATE-----\n"
            "MOCK_CERTIFICATE_DATA_CONVERTED_FROM_PFX\n"
            "-----END CERTIFICATE-----"
        )

        if commit:
            certificate.save()
        return certificate


class BranchForm(forms.ModelForm):
    """Form for creating and editing branch information."""

    class Meta:
        model = models.Branch
        fields = [
            "name",
            "description",
            "sunat_code",
            "address",
            "country",
            "region",
            "subregion",
            "city",
            "phone",
            "email",
            "website",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "sunat_code": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "country": autocomplete.ModelSelect2(
                url="apps.core:country-autocomplete",
                attrs={"class": "form-select", "data-control": "select2"},
            ),
            "region": autocomplete.ModelSelect2(
                url="apps.core:region-autocomplete",
                forward=["country"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Department"),
                },
            ),
            "subregion": autocomplete.ModelSelect2(
                url="apps.core:subregion-autocomplete",
                forward=["region"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("Province"),
                },
            ),
            "city": autocomplete.ModelSelect2(
                url="apps.core:city-autocomplete",
                forward=["country", "region", "subregion"],
                attrs={
                    "class": "form-select",
                    "data-control": "select2",
                    "placeholder": _("District"),
                },
            ),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
        }

    def clean_sunat_code(self) -> str:
        """Validate SUNAT code format (4 digits)."""
        sunat_code = self.cleaned_data.get("sunat_code")
        if sunat_code and not sunat_code.isdigit():
            raise forms.ValidationError(
                _("SUNAT code must contain only digits")
            )
        if sunat_code and len(sunat_code) != 4:
            raise forms.ValidationError(_("SUNAT code must be exactly 4 digits"))
        return sunat_code


class DocumentSeriesForm(forms.ModelForm):
    """Form for creating and editing document series."""

    class Meta:
        model = models.DocumentSeries
        fields = ["document_type", "series_number", "current_correlative"]
        widgets = {
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "series_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("e.g., F001, B001, T001"),
                }
            ),
            "current_correlative": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
        }

    def clean(self) -> dict:
        """
        Validate SUNAT series naming conventions.

        Raises:
            ValidationError: If the series number doesn't match the document type convention.

        Returns:
            dict: Cleaned form data.
        """
        cleaned_data = super().clean()
        document_type = cleaned_data.get("document_type")
        series_number = cleaned_data.get("series_number")

        if document_type and series_number:
            series_number = series_number.upper()
            cleaned_data["series_number"] = series_number

            # SUNAT series naming conventions
            conventions = {
                "01": ("F", _("Factura Electrónica")),  # Factura
                "03": ("B", _("Boleta de Venta Electrónica")),  # Boleta
                "07": (
                    ("F", "B"),
                    _("Nota de Crédito Electrónica"),
                ),  # Nota de Crédito
                "08": (
                    ("F", "B"),
                    _("Nota de Débito Electrónica"),
                ),  # Nota de Débito
                "09": ("T", _("Guía de Remisión Electrónica")),  # Guía de Remisión
            }

            if document_type in conventions:
                required_prefix, doc_name = conventions[document_type]

                # Check if series starts with required prefix(es)
                if isinstance(required_prefix, tuple):
                    if not any(
                        series_number.startswith(prefix)
                        for prefix in required_prefix
                    ):
                        raise forms.ValidationError(
                            _(
                                "For %(doc_type)s, the series must start with %(prefix)s"
                            )
                            % {
                                "doc_type": doc_name,
                                "prefix": _(" or ").join(required_prefix),
                            }
                        )
                else:
                    if not series_number.startswith(required_prefix):
                        raise forms.ValidationError(
                            _(
                                "For %(doc_type)s, the series must start with '%(prefix)s'"
                            )
                            % {"doc_type": doc_name, "prefix": required_prefix}
                        )

            # Validate series format (letter followed by 3 digits)
            if len(series_number) != 4:
                raise forms.ValidationError(
                    _("Series number must be exactly 4 characters (e.g., F001)")
                )

            if not series_number[0].isalpha() or not series_number[1:].isdigit():
                raise forms.ValidationError(
                    _(
                        "Series number must be 1 letter followed by 3 digits (e.g., F001)"
                    )
                )

        return cleaned_data
