from django.urls import path
from . import views
from . import core

app_name = 'payments'

urlpatterns = [
    path('', views.home, name='payments'),
    path('test-payment', views.test_payment, name='test_payment'),
    path('stripe-webhook', core.stripe_webhook, name='stripe_webhook'),
    path('create-payment-intent', core.create_payment_intent, name='paymentintent'),
    path('create-payment-superintent', core.create_payment_superintent, name='paymentsuperintent'),
    path('statement', views.statement, name='statement'),
    path('statement-csv', views.statement_csv, name='statement_csv'),
    path('statement-pdf', views.statement_pdf, name='statement_pdf'),
    path('setup-autotopup', views.setup_autotopup, name='setup_autotopup'),
    path('member-transfer', views.member_transfer, name='member_transfer'),
]
