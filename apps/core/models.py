from cities_light.models import City, Country, Region, SubRegion
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseAddress(models.Model):
    address = models.CharField(_("Address"), max_length=255, blank=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        verbose_name=_("Country"),
        null=True,
        blank=True,
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        verbose_name=_("Department"),
        null=True,
        blank=True,
    )
    subregion = models.ForeignKey(
        SubRegion,
        on_delete=models.SET_NULL,
        verbose_name=_("Province"),
        null=True,
        blank=True,
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        verbose_name=_("District"),
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class BaseContact(models.Model):
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    email = models.EmailField(_("Email"), blank=True)

    class Meta:
        abstract = True


class BaseUserTracked(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created",
        null=True,
        blank=True,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class BaseNameDescription(models.Model):
    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class BaseIsActive(models.Model):
    is_active = models.BooleanField(
        _("Is active"),
        default=True,
        help_text=_("Designates whether this entry is active"),
    )

    class Meta:
        abstract = True
