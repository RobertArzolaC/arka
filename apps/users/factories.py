"""Factories for creating test user instances."""

import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating User instances in tests.

    Attributes:
        email: Unique email address generated using Faker
        first_name: Random first name
        last_name: Random last name
        is_active: User active status (default: True)
        is_staff: Staff status (default: False)
        is_superuser: Superuser status (default: False)
    """

    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create: bool, extracted: str, **kwargs) -> None:
        """
        Set user password after instance creation.

        Args:
            create: Whether to save the instance to the database
            extracted: Password value if provided explicitly
            **kwargs: Additional keyword arguments

        Returns:
            None
        """
        if not create:
            return

        if extracted:
            self.set_password(extracted)
        else:
            self.set_password("testpass123")

    @factory.post_generation
    def groups(self, create: bool, extracted, **kwargs) -> None:
        """
        Add groups to user after instance creation.

        Args:
            create: Whether to save the instance to the database
            extracted: List of groups if provided explicitly
            **kwargs: Additional keyword arguments

        Returns:
            None
        """
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)


class AdminUserFactory(UserFactory):
    """
    Factory for creating admin User instances.

    Inherits from UserFactory and sets is_staff and is_superuser to True.
    """

    is_staff = True
    is_superuser = True
    first_name = "Admin"
    last_name = "User"


class StaffUserFactory(UserFactory):
    """
    Factory for creating staff User instances.

    Inherits from UserFactory and sets is_staff to True.
    """

    is_staff = True
    first_name = "Staff"
    last_name = "User"
