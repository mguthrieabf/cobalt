# pylint: disable=missing-module-docstring,missing-class-docstring
from django.urls import path
from . import views

app_name = "notifications"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("passthrough/<int:id>/", views.passthrough, name="passthrough"),
    path("deleteall", views.deleteall, name="deleteall"),
    path("delete/<int:id>/", views.delete, name="delete"),
]
