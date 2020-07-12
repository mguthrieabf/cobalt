# pylint: disable=missing-module-docstring,missing-class-docstring
from django.urls import path
from . import views

# app_name ='dashboard' # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="dashboard"),
    path("scroll", views.scroll, name="scroll"),
]
