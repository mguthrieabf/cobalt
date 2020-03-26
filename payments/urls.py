from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='payments'),
    path('test-payment', views.test_payment, name='test_payment'),
    path('stripe-webhook', views.stripe_webhook, name='stripe_webhook'),
    path('create-payment-intent', views.create_payment_intent, name='paymentintent'),
    path('statement', views.statement, name='statement'),
    path('test-transaction', views.test_transaction, name='test_transaction'),
]
