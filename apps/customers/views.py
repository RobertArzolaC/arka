from constance import config
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
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
            return models.Account.objects.filter(parent_account=self.request.user.account)
        return models.Account.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = config
        context["entity"] = _("Account")
        context["entity_plural"] = _("Accounts")
        context["back_url"] = reverse_lazy("apps.dashboard:index")
        context["add_entity_url"] = reverse_lazy("apps.customers:account_create")

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
        context["add_entity_url"] = reverse_lazy("apps.customers:company_create")
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
        elif "certificate-certificate_file" in request.FILES or "certificate-certificate_password" in request.POST:
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
            request.POST, request.FILES, instance=certificate, prefix="certificate"
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
