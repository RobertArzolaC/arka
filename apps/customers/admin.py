from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.customers import models


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name",)
    search_fields = ("user__first_name", "user__last_name",)
    autocomplete_fields = ["user"]
    exclude = ("is_removed",)


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for Company model."""

    list_display = (
        "domain",
        "ruc",
        "business_name",
        "commercial_name",
        "regime",
        "created",
    )
    list_filter = ("regime", "created")
    search_fields = ("domain", "ruc", "business_name", "commercial_name")
    exclude = ("is_removed",)
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "domain",
                    "regime",
                    "ruc",
                    "business_name",
                    "commercial_name",
                )
            },
        ),
        (
            _("Location"),
            {"fields": ("address", "country", "region", "city")},
        ),
        (
            _("Contact"),
            {"fields": ("telephone", "email")},
        ),
        (
            _("Logos"),
            {"fields": ("square_logo", "rectangular_logo")},
        ),
    )


@admin.register(models.CompanyCredentials)
class CompanyCredentialsAdmin(admin.ModelAdmin):
    """Admin interface for CompanyCredentials model."""

    list_display = ("company", "sol_user")
    search_fields = ("company__business_name", "sol_user")
    autocomplete_fields = ["company"]


@admin.register(models.CompanyAPICredentials)
class CompanyAPICredentialsAdmin(admin.ModelAdmin):
    """Admin interface for CompanyAPICredentials model."""

    list_display = ("company", "client_id")
    search_fields = ("company__business_name", "client_id")
    autocomplete_fields = ["company"]


@admin.register(models.CompanyCertificate)
class CompanyCertificateAdmin(admin.ModelAdmin):
    """Admin interface for CompanyCertificate model."""

    list_display = ("company", "certificate_file", "created")
    search_fields = ("company__business_name",)
    autocomplete_fields = ["company"]
    readonly_fields = ("certificate_pen",)
