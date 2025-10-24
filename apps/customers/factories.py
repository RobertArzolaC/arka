import factory

from apps.customers import models
from apps.users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker("email")
    password = factory.PostGenerationMethodCall("set_password", "password123")


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    user = factory.SubFactory(UserFactory)
    parent_account = None
    is_organization = False


class CompanyFactory(factory.django.DjangoModelFactory):
    """Factory for creating Company instances for testing."""

    class Meta:
        model = models.Company

    domain = factory.Sequence(lambda n: f"company-{n}")
    regime = factory.Iterator(
        [choice[0] for choice in models.choices.TaxRegimeChoices.choices]
    )
    ruc = factory.Sequence(lambda n: f"20{str(n).zfill(9)}")
    business_name = factory.Faker("company")
    commercial_name = factory.Faker("company")
    address = factory.Faker("street_address")
    phone = factory.Faker("phone_number")
    email = factory.Faker("company_email")


class CompanyCredentialsFactory(factory.django.DjangoModelFactory):
    """Factory for creating CompanyCredentials instances for testing."""

    class Meta:
        model = models.CompanyCredentials

    company = factory.SubFactory(CompanyFactory)
    sol_user = factory.Sequence(lambda n: f"MODDATOS{n}")
    sol_password = factory.Faker("password")


class CompanyAPICredentialsFactory(factory.django.DjangoModelFactory):
    """Factory for creating CompanyAPICredentials instances for testing."""

    class Meta:
        model = models.CompanyAPICredentials

    company = factory.SubFactory(CompanyFactory)
    client_id = factory.Faker("uuid4")
    client_secret = factory.Faker("sha256")


class CompanyCertificateFactory(factory.django.DjangoModelFactory):
    """Factory for creating CompanyCertificate instances for testing."""

    class Meta:
        model = models.CompanyCertificate

    company = factory.SubFactory(CompanyFactory)
    certificate_file = factory.django.FileField(filename="certificate.pfx")
    certificate_password = factory.Faker("password")
    certificate_pen = "-----BEGIN CERTIFICATE-----\nMOCK_DATA\n-----END CERTIFICATE-----"
