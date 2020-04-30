from django.urls import path
from . import views

app_name ='results'

urlpatterns = [
    path('', views.home, name='results'),
]
