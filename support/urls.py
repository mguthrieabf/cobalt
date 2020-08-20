from django.urls import path
from . import views

app_name = "support"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="support"),
    path("rebuild", views.rebuild, name="rebuild"),
]
