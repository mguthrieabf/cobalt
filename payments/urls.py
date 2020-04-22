from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='payments'),
    path('test-payment', views.test_payment, name='test_payment'),
    path('stripe-webhook', views.stripe_webhook, name='stripe_webhook'),
    path('create-payment-intent', views.create_payment_intent, name='paymentintent'),
    path('create-payment-superintent', views.create_payment_superintent, name='paymentsuperintent'),
    path('statement', views.statement, name='statement'),
    path('test-transaction', views.test_transaction, name='test_transaction'),
    path('test-autotopup', views.test_autotopup, name='test_autotopup'),
    path('setup-autotopup', views.setup_autotopup, name='setup_autotopup'),
    path('member-transfer', views.member_transfer, name='member_transfer'),
]
