from django.urls import path
from . import views

app_name = "utils"  # pylint: disable=invalid-name

urlpatterns = [
    path("geo-location", views.geo_location, name="geo_location"),
]
