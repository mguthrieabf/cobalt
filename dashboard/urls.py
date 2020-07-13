# pylint: disable=missing-module-docstring,missing-class-docstring
from django.urls import path
from . import views

# app_name ='dashboard' # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="dashboard"),
    path("scroll1", views.scroll1, name="scroll1"),
    path("scroll2", views.scroll2, name="scroll2"),
]
