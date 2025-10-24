from constance import config
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, UpdateView
from django_filters.views import FilterView

from apps.core import mixins as core_mixins
from apps.customers import filtersets, forms, models


class AccountListView(
    PermissionRequiredMixin, FilterView, LoginRequiredMixin, SuccessMessageMixin
):
    model = models.Account
    permission_required = "customers.view_account"
    filterset_class = filtersets.AccountFilter
    template_name = "customers/account/list.html"
    context_object_name = "accounts"
    paginate_by = 5

    def get_queryset(self):
        if self.request.user.is_organization:
            return models.Account.objects.filter(
                parent_account=self.request.user.account
            )
        return models.Account.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = config
        context["entity"] = _("Account")
        context["entity_plural"] = _("Accounts")
        context["back_url"] = reverse_lazy("apps.dashboard:index")
        context["add_entity_url"] = reverse_lazy(
            "apps.customers:account_create"
        )

        return context


class AccountCreateView(
    PermissionRequiredMixin, FormView, LoginRequiredMixin, SuccessMessageMixin
):
    form_class = forms.AccountCreationForm
    permission_required = "customers.add_account"
    template_name = "customers/account/form.html"
    success_message = _("Account created successfully")
    success_url = reverse_lazy("apps.customers:account_list")

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Account")
        context["back_url"] = reverse_lazy("apps.customers:account_list")
        return context


class AccountUpdateView(
    PermissionRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = models.Account
    context_object_name = "account"
    form_class = forms.AccountUpdateForm
    template_name = "customers/account/form.html"
    permission_required = "customers.change_account"
    success_message = _("Account updated successfully")
    success_url = reverse_lazy("apps.customers:account_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Account")
        context["back_url"] = reverse_lazy("apps.customers:account_list")
        return context


class AccountDeleteView(core_mixins.AjaxDeleteViewMixin):
    model = models.Account


# Company Views


class CompanyListView(
    PermissionRequiredMixin, FilterView, LoginRequiredMixin, SuccessMessageMixin
):
    """List view for companies."""

    model = models.Company
    permission_required = "customers.view_company"
    filterset_class = filtersets.CompanyFilter
    template_name = "customers/company/list.html"
    context_object_name = "companies"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = config
        context["entity"] = _("Company")
        context["entity_plural"] = _("Companies")
        context["back_url"] = reverse_lazy("apps.dashboard:index")
        context["add_entity_url"] = reverse_lazy(
            "apps.customers:company_create"
        )
        return context


class CompanyCreateView(
    PermissionRequiredMixin, FormView, LoginRequiredMixin, SuccessMessageMixin
):
    """View for creating a new company."""

    form_class = forms.CompanyForm
    permission_required = "customers.add_company"
    template_name = "customers/company/form.html"
    success_message = _("Company created successfully")
    success_url = reverse_lazy("apps.customers:company_list")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Company")
        context["back_url"] = reverse_lazy("apps.customers:company_list")
        context["form_title"] = _("Add Company")
        return context


class CompanyUpdateView(
    PermissionRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View for updating company information with tabs."""

    model = models.Company
    context_object_name = "company"
    form_class = forms.CompanyUpdateForm
    template_name = "customers/company/update.html"
    permission_required = "customers.change_company"
    success_message = _("Company updated successfully")

    def get_success_url(self):
        return reverse_lazy(
            "apps.customers:company_update", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Company")
        context["back_url"] = reverse_lazy("apps.customers:company_list")

        # Initialize related forms
        try:
            credentials = self.object.credentials
        except models.CompanyCredentials.DoesNotExist:
            credentials = models.CompanyCredentials(company=self.object)

        try:
            api_credentials = self.object.api_credentials
        except models.CompanyAPICredentials.DoesNotExist:
            api_credentials = models.CompanyAPICredentials(company=self.object)

        try:
            certificate = self.object.certificate
        except models.CompanyCertificate.DoesNotExist:
            certificate = models.CompanyCertificate(company=self.object)

        context["credentials_form"] = forms.CompanyCredentialsForm(
            instance=credentials, prefix="credentials"
        )
        context["api_credentials_form"] = forms.CompanyAPICredentialsForm(
            instance=api_credentials, prefix="api_credentials"
        )
        context["certificate_form"] = forms.CompanyCertificateForm(
            instance=certificate, prefix="certificate"
        )

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Determine which form was submitted based on prefix
        if "credentials-sol_user" in request.POST:
            return self.handle_credentials_form(request)
        elif "api_credentials-client_id" in request.POST:
            return self.handle_api_credentials_form(request)
        elif (
            "certificate-certificate_file" in request.FILES
            or "certificate-certificate_password" in request.POST
        ):
            return self.handle_certificate_form(request)
        else:
            # Handle main company form
            return super().post(request, *args, **kwargs)

    def handle_credentials_form(self, request):
        """Handle SUNAT credentials form submission."""
        try:
            credentials = self.object.credentials
        except models.CompanyCredentials.DoesNotExist:
            credentials = models.CompanyCredentials(company=self.object)

        form = forms.CompanyCredentialsForm(
            request.POST, instance=credentials, prefix="credentials"
        )

        if form.is_valid():
            form.save()
            from django.contrib import messages

            messages.success(request, _("Credentials updated successfully"))
            return self.form_valid(form)

        return self.render_to_response(self.get_context_data())

    def handle_api_credentials_form(self, request):
        """Handle API credentials form submission."""
        try:
            api_credentials = self.object.api_credentials
        except models.CompanyAPICredentials.DoesNotExist:
            api_credentials = models.CompanyAPICredentials(company=self.object)

        form = forms.CompanyAPICredentialsForm(
            request.POST, instance=api_credentials, prefix="api_credentials"
        )

        if form.is_valid():
            form.save()
            from django.contrib import messages

            messages.success(request, _("API Credentials updated successfully"))
            return self.form_valid(form)

        return self.render_to_response(self.get_context_data())

    def handle_certificate_form(self, request):
        """Handle certificate form submission."""
        try:
            certificate = self.object.certificate
        except models.CompanyCertificate.DoesNotExist:
            certificate = models.CompanyCertificate(company=self.object)

        form = forms.CompanyCertificateForm(
            request.POST,
            request.FILES,
            instance=certificate,
            prefix="certificate",
        )

        if form.is_valid():
            form.save()
            from django.contrib import messages

            messages.success(request, _("Certificate updated successfully"))
            return self.form_valid(form)

        return self.render_to_response(self.get_context_data())


class CompanyDeleteView(core_mixins.AjaxDeleteViewMixin):
    """View for deleting a company."""

    model = models.Company


class BranchListView(
    PermissionRequiredMixin, FilterView, LoginRequiredMixin, SuccessMessageMixin
):
    """List view for branches within a company (displayed in tab)."""

    model = models.Branch
    permission_required = "customers.view_branch"
    template_name = "customers/branch/list.html"
    context_object_name = "branches"
    paginate_by = 10

    def get_queryset(self):
        """Filter branches by company."""
        company_id = self.kwargs.get("company_pk")
        return models.Branch.objects.filter(company_id=company_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get("company_pk")
        context["company"] = models.Company.objects.get(pk=company_id)
        context["entity"] = _("Branch")
        context["entity_plural"] = _("Branches")
        context["back_url"] = reverse_lazy("apps.customers:company_list")
        context["add_entity_url"] = reverse_lazy(
            "apps.customers:branch_create", kwargs={"company_pk": company_id}
        )
        return context


class BranchCreateView(
    PermissionRequiredMixin, FormView, LoginRequiredMixin, SuccessMessageMixin
):
    """View for creating a new branch."""

    form_class = forms.BranchForm
    permission_required = "customers.add_branch"
    template_name = "customers/branch/form.html"
    success_message = _("Branch created successfully")

    def get_success_url(self):
        company_id = self.kwargs.get("company_pk")
        return (
            reverse_lazy(
                "apps.customers:company_update", kwargs={"pk": company_id}
            )
            + "?tab=branches"
        )

    def form_valid(self, form):
        company_id = self.kwargs.get("company_pk")
        branch = form.save(commit=False)
        branch.company_id = company_id
        branch.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get("company_pk")
        context["company"] = models.Company.objects.get(pk=company_id)
        context["entity"] = _("Branch")
        context["back_url"] = (
            reverse_lazy(
                "apps.customers:company_update", kwargs={"pk": company_id}
            )
            + "?tab=branches"
        )
        context["form_title"] = _("Add Branch")
        return context


class BranchUpdateView(
    PermissionRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    """View for updating branch information and managing document series."""

    model = models.Branch
    context_object_name = "branch"
    form_class = forms.BranchForm
    template_name = "customers/branch/update.html"
    permission_required = "customers.change_branch"
    success_message = _("Branch updated successfully")

    def get_success_url(self):
        return reverse_lazy(
            "apps.customers:branch_update",
            kwargs={"company_pk": self.object.company_id, "pk": self.object.pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Branch")
        context["company"] = self.object.company

        # Build correct back URL to company update with branches tab
        company_branches_url = (
            reverse_lazy(
                "apps.customers:company_update",
                kwargs={"pk": self.object.company_id},
            )
            + "?tab=branches"
        )
        context["back_url"] = company_branches_url

        # Custom breadcrumbs to avoid incorrect auto-generated URLs
        context["custom_breadcrumbs"] = [
            {
                "title": _("Dashboard"),
                "url": reverse_lazy("apps.dashboard:index"),
                "is_active": False,
            },
            {
                "title": _("Company List"),
                "url": reverse_lazy("apps.customers:company_list"),
                "is_active": False,
            },
            {
                "title": _("Branch List"),
                "url": company_branches_url,
                "is_active": False,
            },
            {
                "title": _("Branch Update"),
                "url": "",
                "is_active": True,
            },
        ]

        # Get all document series for this branch
        context["document_series"] = models.DocumentSeries.objects.filter(
            branch=self.object
        )

        # Form for adding new series
        context["series_form"] = forms.DocumentSeriesForm()

        return context


class BranchDeleteView(core_mixins.AjaxDeleteViewMixin):
    """View for deleting a branch."""

    model = models.Branch


class DocumentSeriesCreateView(
    PermissionRequiredMixin, LoginRequiredMixin, View
):
    """AJAX view for creating a document series."""

    permission_required = "customers.add_documentseries"

    def post(self, request, company_pk, branch_pk):
        """
        Handle AJAX POST request to create a new document series.

        Args:
            request: HTTP request object.
            company_pk: Company primary key.
            branch_pk: Branch primary key.

        Returns:
            JsonResponse: JSON response with success status and data.
        """

        try:
            branch = models.Branch.objects.get(
                pk=branch_pk, company_id=company_pk
            )
            form = forms.DocumentSeriesForm(request.POST)

            if form.is_valid():
                try:
                    series = form.save(commit=False)
                    series.branch = branch
                    series.save()

                    return JsonResponse(
                        {
                            "success": True,
                            "message": str(
                                _("Document series added successfully")
                            ),
                            "series": {
                                "id": series.id,
                                "document_type": series.get_document_type_display(),
                                "series_number": series.series_number,
                                "current_correlative": series.current_correlative,
                            },
                        }
                    )
                except IntegrityError:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": str(
                                _(
                                    "A series with this document type and number already exists for this branch"
                                )
                            ),
                        },
                        status=400,
                    )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "errors": form.errors,
                    },
                    status=400,
                )
        except models.Branch.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": str(_("Branch not found"))},
                status=404,
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": str(e)}, status=500
            )


class DocumentSeriesDeleteView(
    PermissionRequiredMixin, LoginRequiredMixin, View
):
    """AJAX view for deleting a document series."""

    permission_required = "customers.delete_documentseries"

    def delete(self, request, company_pk, branch_pk, pk):  # noqa: ARG002
        """
        Handle AJAX DELETE request to remove a document series.

        Args:
            request: HTTP request object (required by View interface).
            company_pk: Company primary key.
            branch_pk: Branch primary key.
            pk: Document series primary key.

        Returns:
            JsonResponse: JSON response with success status.
        """
        try:
            series = models.DocumentSeries.objects.get(
                pk=pk, branch_id=branch_pk, branch__company_id=company_pk
            )
            series.delete()

            return JsonResponse(
                {
                    "success": True,
                    "message": str(_("Document series deleted successfully")),
                }
            )
        except models.DocumentSeries.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": str(_("Document series not found")),
                },
                status=404,
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": str(e)}, status=500
            )
