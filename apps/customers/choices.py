from django.db import models
from django.utils.translation import gettext_lazy as _


class TaxRegimeChoices(models.TextChoices):
    """Tax regime choices for companies in Peru."""

    ESPECIAL = "ESPECIAL", _("Especial")
    GENERAL = "GENERAL", _("General")
    MYPE = "MYPE", _("MYPE")
    RUS = "RUS", _("RUS")
