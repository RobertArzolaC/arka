from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.users import models as user_models
from apps.users.models import User


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users in Django admin."""

    class Meta:
        model = User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users in Django admin."""

    class Meta:
        model = User
        fields = ("email",)


class UserSettingsForm(forms.ModelForm):
    """Form for user profile settings."""

    first_name = forms.CharField(max_length=30, label=_("First name"))
    last_name = forms.CharField(
        max_length=30, label=_("Last name"), required=False
    )

    class Meta:
        model = user_models.User
        fields = ["first_name", "last_name"]


class UserCreateForm(forms.ModelForm):
    """
    Form for creating new users with password validation.

    Includes fields for user details, password confirmation, and group assignment.
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label=_("First Name"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("First Name")}
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label=_("Last Name"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Last Name")}
        ),
    )
    email = forms.EmailField(
        required=True,
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("Email")}
        ),
    )
    password = forms.CharField(
        required=True,
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Password")}
        ),
        help_text=_(
            "Password must be at least 8 characters long and cannot be entirely numeric."
        ),
    )
    confirm_password = forms.CharField(
        required=True,
        label=_("Confirm Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Confirm Password"),
            }
        ),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label=_("Groups"),
        widget=forms.CheckboxSelectMultiple(),
        help_text=_(
            "Select groups to assign roles (Administrador, Colaborador, etc.)"
        ),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "groups"]

    def clean_email(self) -> str:
        """
        Validate that the email is unique.

        Returns:
            str: Cleaned email address

        Raises:
            ValidationError: If email already exists
        """
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("A user with this email already exists."))
        return email

    def clean_password(self) -> str:
        """
        Validate password using Django's password validators.

        Returns:
            str: Cleaned password

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password)
        return password

    def clean(self) -> dict:
        """
        Validate that password and confirm_password match.

        Returns:
            dict: Cleaned form data

        Raises:
            ValidationError: If passwords don't match
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError(
                {"confirm_password": _("Passwords do not match.")}
            )

        return cleaned_data

    def save(self, commit: bool = True) -> User:
        """
        Save the user instance with hashed password and assigned groups.

        Args:
            commit: Whether to save to database

        Returns:
            User: The created user instance
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            # Assign groups after user is saved
            if self.cleaned_data.get("groups"):
                user.groups.set(self.cleaned_data["groups"])

        return user


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating existing users.

    Password fields are optional - if left blank, password remains unchanged.
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label=_("First Name"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("First Name")}
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label=_("Last Name"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Last Name")}
        ),
    )
    email = forms.EmailField(
        required=True,
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("Email")}
        ),
    )
    password = forms.CharField(
        required=False,
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("New Password")}
        ),
        help_text=_(
            "Leave blank to keep current password. Password must be at least 8 characters."
        ),
    )
    confirm_password = forms.CharField(
        required=False,
        label=_("Confirm Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Confirm New Password"),
            }
        ),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label=_("Groups"),
        widget=forms.CheckboxSelectMultiple(),
        help_text=_(
            "Select groups to assign roles (Administrador, Colaborador, etc.)"
        ),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "groups"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set initial groups."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["groups"].initial = self.instance.groups.all()

    def clean_email(self) -> str:
        """
        Validate that email is unique (excluding current user).

        Returns:
            str: Cleaned email address

        Raises:
            ValidationError: If email already exists for another user
        """
        email = self.cleaned_data.get("email")
        if (
            User.objects.filter(email=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError(_("A user with this email already exists."))
        return email

    def clean_password(self) -> str:
        """
        Validate password if provided.

        Returns:
            str: Cleaned password

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password)
        return password

    def clean(self) -> dict:
        """
        Validate that password and confirm_password match if password is provided.

        Returns:
            dict: Cleaned form data

        Raises:
            ValidationError: If passwords don't match
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError(
                {"confirm_password": _("Passwords do not match.")}
            )

        return cleaned_data

    def save(self, commit: bool = True) -> User:
        """
        Save the user instance, updating password only if provided.

        Args:
            commit: Whether to save to database

        Returns:
            User: The updated user instance
        """
        user = super().save(commit=False)

        # Update password only if provided
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)

        if commit:
            user.save()
            # Update groups
            user.groups.set(self.cleaned_data.get("groups", []))

        return user
