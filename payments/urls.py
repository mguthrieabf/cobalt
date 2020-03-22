from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='payments'),
    path('checkout', views.checkout, name='checkout'),
    path('test-payment', views.test_payment, name='test_payment'),
    path('create-payment-intent', views.create_payment_intent, name='paymentintent'),
]
