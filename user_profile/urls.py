from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='user_profile'),
    path('public-profile/<int:pk>/', views.public_profile, name='public_profile'),
]
