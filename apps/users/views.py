from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    TemplateView,
    UpdateView,
    View,
)
from django_filters.views import FilterView

from apps.customers import forms as customer_forms
from apps.users import filters, forms
from apps.users.models import User


class ProfileView(LoginRequiredMixin, TemplateView):
    """View for displaying user profile."""

    template_name = "users/profile.html"
    paginate_by = 6

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get context data for the template.

        Args:
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Context dictionary
        """
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Profile")
        context["back_url"] = reverse_lazy("apps.dashboard:index")

        return context


class SettingsView(SuccessMessageMixin, LoginRequiredMixin, View):
    """View for updating user settings."""

    template_name = "users/settings.html"
    success_message = _("Settings updated successfully")
    success_url = reverse_lazy("apps.users:settings")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get context data for the template.

        Args:
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Context dictionary
        """
        user = self.request.user

        context = {
            "entity": _("Settings"),
            "back_url": reverse_lazy("apps.dashboard:index"),
            "user_form": forms.UserSettingsForm(instance=user),
        }

        if user.is_account:
            context["account_form"] = customer_forms.AccountSettingsForm(
                instance=user.account
            )

        context.update(kwargs)
        return context

    def get(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """
        Handle GET request.

        Args:
            request: The HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            HttpResponse: The rendered template
        """
        return render(request, self.template_name, self.get_context_data())

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """
        Handle POST request.

        Args:
            request: The HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            HttpResponse: Redirect or rendered template
        """
        try:
            user = request.user

            user_form = forms.UserSettingsForm(
                request.POST, request.FILES, instance=user
            )
            if user_form.is_valid():
                user_form.save()

            if user.is_account:
                customer_form = customer_forms.AccountSettingsForm(
                    request.POST, request.FILES, instance=user.account
                )

                if customer_form.is_valid():
                    customer_form.save()

            messages.success(request, self.success_message)
            return redirect(self.success_url)
        except Exception as e:
            messages.error(request, f"Error updating settings: {str(e)}")

        return render(request, self.template_name, self.get_context_data())


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """View for listing all users with filtering capabilities."""

    model = User
    template_name = "users/list.html"
    context_object_name = "users"
    paginate_by = 10
    filterset_class = filters.UserFilter
    permission_required = "users.view_user"

    def get_queryset(self) -> QuerySet[User]:
        """
        Get the queryset of users.

        Returns:
            QuerySet: Filtered queryset of users
        """
        queryset = (
            User.objects.select_related()
            .prefetch_related("groups")
            .order_by("-date_joined")
        )
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get context data for the template.

        Args:
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Context dictionary
        """
        context = super().get_context_data(**kwargs)
        context["entity"] = _("User")
        context["entity_plural"] = _("Users")
        context["add_entity_url"] = reverse_lazy("apps.users:user_create")
        context["back_url"] = reverse_lazy("apps.dashboard:index")

        return context


class UserCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """View for creating new users."""

    model = User
    form_class = forms.UserCreateForm
    template_name = "users/form.html"
    success_url = reverse_lazy("apps.users:user_list")
    success_message = _("User created successfully")
    permission_required = "users.add_user"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get context data for the template.

        Args:
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Context dictionary
        """
        context = super().get_context_data(**kwargs)
        context["entity"] = _("User")
        context["back_url"] = reverse_lazy("apps.users:user_list")
        context["is_create"] = True

        return context


class UserUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View for updating existing users."""

    model = User
    form_class = forms.UserUpdateForm
    template_name = "users/form.html"
    success_url = reverse_lazy("apps.users:user_list")
    success_message = _("User updated successfully")
    permission_required = "users.change_user"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get context data for the template.

        Args:
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Context dictionary
        """
        context = super().get_context_data(**kwargs)
        context["entity"] = _("User")
        context["back_url"] = reverse_lazy("apps.users:user_list")
        context["is_create"] = False

        return context


class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """View for deleting users."""

    model = User
    success_url = reverse_lazy("apps.users:user_list")
    permission_required = "users.delete_user"

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """
        Handle POST request for user deletion.

        Args:
            request: The HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            HttpResponse: Redirect to user list
        """
        try:
            user = self.get_object()
            if user == request.user:
                messages.error(request, _("You cannot delete your own account"))
                return redirect(self.success_url)

            user.delete()
            messages.success(request, _("User deleted successfully"))
        except Exception as e:
            messages.error(request, f"Error deleting user: {str(e)}")

        return redirect(self.success_url)
