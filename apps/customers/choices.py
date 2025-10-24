from django.db import models
from django.utils.translation import gettext_lazy as _


class TaxRegimeChoices(models.TextChoices):
    """Tax regime choices for companies in Peru."""

    ESPECIAL = "ESPECIAL", _("Especial")
    GENERAL = "GENERAL", _("General")
    MYPE = "MYPE", _("MYPE")
    RUS = "RUS", _("RUS")


class DocumentTypeChoices(models.TextChoices):
    """Electronic document type choices for Peru (SUNAT)."""

    FACTURA = "01", _("Factura Electrónica")
    BOLETA = "03", _("Boleta de Venta Electrónica")
    NOTA_CREDITO = "07", _("Nota de Crédito Electrónica")
    NOTA_DEBITO = "08", _("Nota de Débito Electrónica")
    GUIA_REMISION = "09", _("Guía de Remisión Electrónica")
