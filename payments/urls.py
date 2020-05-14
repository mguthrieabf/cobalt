from django.urls import path
from . import views
from . import core

app_name = 'payments'

urlpatterns = [
    path('', views.home, name='payments'),
    path('test-payment', views.test_payment, name='test_payment'),
    path('stripe-webhook', core.stripe_webhook, name='stripe_webhook'),
    path('create-payment-intent', core.stripe_manual_payment_intent, name='paymentintent'),
    path('create-payment-superintent', core.stripe_auto_payment_intent, name='paymentsuperintent'),
    path('statement', views.statement, name='statement'),
    path('statement-csv', views.statement_csv, name='statement_csv'),
    path('statement-pdf', views.statement_pdf, name='statement_pdf'),
    path('setup-autotopup', views.setup_autotopup, name='setup_autotopup'),
    path('update-auto-amount', views.update_auto_amount, name='update_auto_amount'),
    path('member-transfer', views.member_transfer, name='member_transfer'),
]
