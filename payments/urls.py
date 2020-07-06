# pylint: disable=missing-module-docstring,missing-class-docstring
from django.urls import path
from . import views
from . import core

app_name = "payments"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.statement, name="payments"),
    path("test-payment", views.test_payment, name="test_payment"),
    path("stripe-webhook", core.stripe_webhook, name="stripe_webhook"),
    path(
        "create-payment-intent", core.stripe_manual_payment_intent, name="paymentintent"
    ),
    path(
        "create-payment-superintent",
        core.stripe_auto_payment_intent,
        name="paymentsuperintent",
    ),
    path("statement", views.statement, name="statement"),
    path(
        "statement-admin-view/<int:member_id>",
        views.statement_admin_view,
        name="statement_admin_view",
    ),
    path("statement-csv", views.statement_csv, name="statement_csv"),
    path("statement-pdf", views.statement_pdf, name="statement_pdf"),
    path("setup-autotopup", views.setup_autotopup, name="setup_autotopup"),
    path("update-auto-amount", views.update_auto_amount, name="update_auto_amount"),
    path("member-transfer", views.member_transfer, name="member_transfer"),
    path("manual-topup", views.manual_topup, name="manual_topup"),
    path("cancel-autotopup", views.cancel_auto_top_up, name="cancel_autotopup"),
    path(
        "statement-admin-summary",
        views.statement_admin_summary,
        name="statement_admin_summary",
    ),
    path("statement-org/<int:org_id>/", views.statement_org, name="statement_org"),
    path(
        "statement-org-summary/<int:org_id>/<str:range>",
        views.statement_org_summary_ajax,
        name="statement_org_summary_ajax",
    ),
]
