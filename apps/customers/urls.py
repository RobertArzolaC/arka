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
]
