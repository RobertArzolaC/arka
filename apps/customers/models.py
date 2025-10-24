from allauth.account.models import EmailAddress
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from model_utils.models import SoftDeletableModel, TimeStampedModel

from apps.core import models as core_models
from apps.customers import choices, validators
from apps.users.models import User


class Account(SoftDeletableModel, TimeStampedModel):
    user = models.OneToOneField(
        User,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="account",
    )

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        ordering = ("user__last_name", "user__first_name")

    def __str__(self):
        return self.user.get_full_name()

    @cached_property
    def full_name(self):
        return self.user.get_full_name()

    @cached_property
    def is_email_verified(self):
        return EmailAddress.objects.filter(
            user=self.user, verified=True
        ).exists()


class Company(
    core_models.BaseAddress,
    core_models.BaseContact,
    SoftDeletableModel,
    TimeStampedModel,
):
    """Model representing a company/organization in the system."""

    domain = models.CharField(
        max_length=100,
        validators=[validators.domain_validator],
        verbose_name=_("Domain"),
        help_text=_("Unique domain for accessing the system"),
    )
    regime = models.CharField(
        max_length=20,
        choices=choices.TaxRegimeChoices.choices,
        verbose_name=_("Tax Regime"),
    )
    ruc = models.CharField(
        max_length=11, verbose_name=_("RUC"), help_text=_("Tax ID Number")
    )
    business_name = models.CharField(
        max_length=255, verbose_name=_("Business Name")
    )
    commercial_name = models.CharField(
        max_length=255, verbose_name=_("Commercial Name")
    )

    # Logo fields
    square_logo = models.ImageField(
        upload_to="companies/logos/square/",
        null=True,
        blank=True,
        verbose_name=_("Square Logo"),
        help_text=_("Recommended size: 150x150px"),
    )
    rectangular_logo = models.ImageField(
        upload_to="companies/logos/rectangular/",
        null=True,
        blank=True,
        verbose_name=_("Rectangular Logo"),
        help_text=_("Recommended size: 350x167px"),
    )

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ("business_name",)
        constraints = [
            models.UniqueConstraint(
                fields=["ruc"],
                condition=models.Q(is_removed=False),
                name="unique_ruc_when_not_removed",
            ),
            models.UniqueConstraint(
                fields=["domain"],
                condition=models.Q(is_removed=False),
                name="unique_domain_when_not_removed",
            ),
        ]

    def __str__(self) -> str:
        return self.commercial_name or self.business_name


class CompanyCredentials(TimeStampedModel):
    """SUNAT credentials for electronic document emission."""

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="credentials",
        verbose_name=_("Company"),
    )
    sol_user = models.CharField(
        max_length=100, verbose_name=_("Secondary Sol User")
    )
    sol_password = models.CharField(
        max_length=255, verbose_name=_("Sol Password")
    )

    class Meta:
        verbose_name = _("Company Credentials")
        verbose_name_plural = _("Company Credentials")

    def __str__(self) -> str:
        return f"Credentials for {self.company.commercial_name}"


class CompanyAPICredentials(TimeStampedModel):
    """API credentials for SUNAT electronic shipping guides."""

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="api_credentials",
        verbose_name=_("Company"),
    )
    client_id = models.CharField(max_length=255, verbose_name=_("Client ID"))
    client_secret = models.CharField(
        max_length=255, verbose_name=_("Client Secret")
    )

    class Meta:
        verbose_name = _("Company API Credentials")
        verbose_name_plural = _("Company API Credentials")

    def __str__(self) -> str:
        return f"API Credentials for {self.company.commercial_name}"


class CompanyCertificate(TimeStampedModel):
    """Digital certificate for signing electronic documents."""

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="certificate",
        verbose_name=_("Company"),
    )
    certificate_file = models.FileField(
        upload_to="companies/certificates/",
        verbose_name=_("Certificate File"),
        help_text=_("PFX or P12 format"),
    )
    certificate_password = models.CharField(
        max_length=255, verbose_name=_("Certificate Password")
    )
    certificate_pen = models.TextField(
        blank=True,
        verbose_name=_("Certificate PEN"),
        help_text=_("Converted PEN format for SUNAT"),
    )

    class Meta:
        verbose_name = _("Company Certificate")
        verbose_name_plural = _("Company Certificates")

    def __str__(self) -> str:
        return f"Certificate for {self.company.commercial_name}"


class Branch(
    core_models.BaseNameDescription,
    core_models.BaseAddress,
    core_models.BaseContact,
    SoftDeletableModel,
    TimeStampedModel,
):
    """Model representing a company's branch or warehouse."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="branches",
        verbose_name=_("Company"),
    )
    sunat_code = models.CharField(
        max_length=10,
        verbose_name=_("SUNAT Establishment Code"),
        help_text=_(
            "Code for SUNAT annex establishment (e.g., '0000' for main branch)"
        ),
    )
    website = models.URLField(
        max_length=255,
        blank=True,
        verbose_name=_("Website"),
    )

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")
        ordering = ("company", "sunat_code")
        unique_together = ("company", "sunat_code")

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.sunat_code}) - {self.company.commercial_name}"
        )


class DocumentSeries(SoftDeletableModel, TimeStampedModel):
    """Model to manage document series for each branch."""

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="document_series",
        verbose_name=_("Branch"),
    )
    document_type = models.CharField(
        max_length=2,
        choices=choices.DocumentTypeChoices.choices,
        verbose_name=_("Document Type"),
    )
    series_number = models.CharField(
        max_length=10,
        verbose_name=_("Series Number"),
        help_text=_("Series code (e.g., 'F001', 'B001', 'T001')"),
    )
    current_correlative = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Current Correlative"),
        help_text=_("Next sequential number to be used for this series"),
    )

    class Meta:
        verbose_name = _("Document Series")
        verbose_name_plural = _("Document Series")
        ordering = ("branch", "document_type", "series_number")
        unique_together = ("branch", "document_type", "series_number")

    def __str__(self) -> str:
        return f"{self.get_document_type_display()} - {self.series_number} ({self.branch.name})"

    def get_next_correlative(self) -> str:
        """
        Get the next correlative number and increment the counter.

        Returns:
            str: Formatted correlative number with leading zeros (8 digits).
        """
        correlative = self.current_correlative
        self.current_correlative += 1
        self.save(update_fields=["current_correlative"])
        return str(correlative).zfill(8)
