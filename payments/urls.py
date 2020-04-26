from django.urls import path
from . import views
from . import core


urlpatterns = [
    path('', views.home, name='payments'),
    path('test-payment', views.test_payment, name='test_payment'),
    path('stripe-webhook', core.stripe_webhook, name='stripe_webhook'),
    path('create-payment-intent', core.create_payment_intent, name='paymentintent'),
    path('create-payment-superintent', core.create_payment_superintent, name='paymentsuperintent'),
    path('statement', views.statement, name='statement'),
    path('test-transaction', views.test_transaction, name='test_transaction'),
    path('test-autotopup', views.test_autotopup, name='test_autotopup'),
    path('setup-autotopup', views.setup_autotopup, name='setup_autotopup'),
    path('member-transfer', views.member_transfer, name='member_transfer'),
]
