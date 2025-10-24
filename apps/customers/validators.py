from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

domain_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9-]+$",
    message=_("Domain must contain only alphanumeric characters and hyphens."),
)
