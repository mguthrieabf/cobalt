from django.urls import path
from . import views

app_name = "events"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="events"),
]
