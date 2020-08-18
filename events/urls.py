from django.urls import path
from . import views

app_name = "events"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="events"),
    path("congress/view/<int:congress_id>", views.view_congress, name="view_congress"),
    path(
        "congress/preview/<int:congress_id>",
        views.preview_congress,
        name="preview_congress",
    ),
    path("congress/edit/<int:congress_id>", views.edit_congress, name="edit_congress"),
    path(
        "congress/delete/<int:congress_id>",
        views.delete_congress,
        name="delete_congress",
    ),
    path("congress/create2", views.create_congress, name="create_congress"),
    path(
        "congress/create/wizard",
        views.create_congress_wizard,
        name="create_congress_wizard",
    ),
    path(
        "congress/create/wizard/<int:step>",
        views.create_congress_wizard,
        name="create_congress_wizard",
    ),
    path(
        "congress/create/wizard/<int:congress_id>/<int:step>",
        views.create_congress_wizard,
        name="create_congress_wizard",
    ),
    path(
        "congress/get-conveners/<int:org_id>",
        views.get_conveners_ajax,
        name="get_conveners_ajax",
    ),
    path(
        "congress/create/get-congress-master/<int:org_id>",
        views.get_congress_master_ajax,
        name="get_congress_master_ajax",
    ),
    path(
        "congress/create/get-congress/<int:congress_id>",
        views.get_congress_ajax,
        name="get_congress_ajax",
    ),
    path(
        "congress/create/add-event/<int:congress_id>",
        views.create_event,
        name="create_event",
    ),
    path(
        "congress/create/delete-event",
        views.delete_event_ajax,
        name="delete_event_ajax",
    ),
]
