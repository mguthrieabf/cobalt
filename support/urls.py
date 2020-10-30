from django.urls import path
from . import views

app_name = "support"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="support"),
    path("browser-errors", views.browser_errors, name="browser_errors"),
    path("search", views.search, name="search"),
    path("cookies", views.cookies, name="cookies"),
    path("guidelines", views.guidelines, name="guidelines"),
    path("acceptable-use", views.acceptable_use, name="acceptable_use"),
]
