from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='masterpoints'),
    path('abf_lookup', views.abf_lookup, name='abf_lookup'),
]
