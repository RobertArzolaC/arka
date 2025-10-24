from django.urls import path

from apps.customers import views

app_name = "apps.customers"

urlpatterns = [
    # Accounts URLs
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path(
        "accounts/create/",
        views.AccountCreateView.as_view(),
        name="account_create",
    ),
    path(
        "accounts/update/<int:pk>/",
        views.AccountUpdateView.as_view(),
        name="account_update",
    ),
    path(
        "accounts/<int:pk>/delete/",
        views.AccountDeleteView.as_view(),
        name="account_delete",
    ),
    # Companies URLs
    path("companies/", views.CompanyListView.as_view(), name="company_list"),
    path(
        "companies/add/",
        views.CompanyCreateView.as_view(),
        name="company_create",
    ),
    path(
        "companies/<int:pk>/edit/",
        views.CompanyUpdateView.as_view(),
        name="company_update",
    ),
    path(
        "companies/<int:pk>/delete/",
        views.CompanyDeleteView.as_view(),
        name="company_delete",
    ),
    # Branch URLs
    path(
        "companies/<int:company_pk>/branches/",
        views.BranchListView.as_view(),
        name="branch_list",
    ),
    path(
        "companies/<int:company_pk>/branches/add/",
        views.BranchCreateView.as_view(),
        name="branch_create",
    ),
    path(
        "companies/<int:company_pk>/branches/<int:pk>/edit/",
        views.BranchUpdateView.as_view(),
        name="branch_update",
    ),
    path(
        "companies/<int:company_pk>/branches/<int:pk>/delete/",
        views.BranchDeleteView.as_view(),
        name="branch_delete",
    ),
    # Document Series URLs (AJAX)
    path(
        "companies/<int:company_pk>/branches/<int:branch_pk>/series/add/",
        views.DocumentSeriesCreateView.as_view(),
        name="document_series_create",
    ),
    path(
        "companies/<int:company_pk>/branches/<int:branch_pk>/series/<int:pk>/delete/",
        views.DocumentSeriesDeleteView.as_view(),
        name="document_series_delete",
    ),
]
