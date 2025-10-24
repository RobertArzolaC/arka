"""Filters for user listing and search functionality."""

import django_filters
from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


class UserFilter(django_filters.FilterSet):
    """
    FilterSet for filtering users in the user list view.

    Provides filters for:
    - Name/email search
    - Active status
    - Groups (roles)
    - Staff status
    """

    name_search = django_filters.CharFilter(
        method="filter_name_or_email",
        label=_("Search"),
        widget=django_filters.widgets.forms.TextInput(
            attrs={
                "class": "form-control w-250px ps-12",
                "placeholder": _("Search Name or Email"),
            }
        ),
    )

    is_active = django_filters.BooleanFilter(
        label=_("Status"),
        widget=django_filters.widgets.forms.Select(
            choices=[
                ("", _("All Statuses")),
                ("true", _("Active")),
                ("false", _("Inactive")),
            ],
            attrs={"class": "form-select"},
        ),
    )

    groups = django_filters.ModelChoiceFilter(
        queryset=Group.objects.all(),
        label=_("Group"),
        empty_label=_("All Groups"),
        widget=django_filters.widgets.forms.Select(
            attrs={"class": "form-select"}
        ),
    )

    is_staff = django_filters.BooleanFilter(
        label=_("User Type"),
        widget=django_filters.widgets.forms.Select(
            choices=[
                ("", _("All Users")),
                ("true", _("Staff Only")),
                ("false", _("Non-Staff Only")),
            ],
            attrs={"class": "form-select"},
        ),
    )

    class Meta:
        model = User
        fields = ["name_search", "is_active", "groups", "is_staff"]

    def filter_name_or_email(self, queryset, name, value):
        """
        Filter users by first name, last name, or email.

        Args:
            queryset: The queryset to filter
            name: The filter field name
            value: The search value

        Returns:
            QuerySet: Filtered queryset
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(email__icontains=value)
        )
