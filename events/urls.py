from django.urls import path
from . import views

app_name = "events"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="events"),
    path("congress/view/<int:congress_id>", views.view_congress, name="view_congress"),
    path("congress/edit/<int:congress_id>", views.edit_congress, name="edit_congress"),
    path("congress/create", views.create_congress, name="create_congress"),
]
