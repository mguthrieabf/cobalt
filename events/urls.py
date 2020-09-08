from django.urls import path
from . import views, ajax

app_name = "events"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="events"),
    path("congress/view/<int:congress_id>", views.view_congress, name="view_congress"),
    path(
        "congress/view/<int:congress_id>/<int:fullscreen>",
        views.view_congress,
        name="view_congress",
    ),
    path(
        "congress/event/enter/<int:congress_id>/<int:event_id>",
        views.enter_event,
        name="enter_event",
    ),
    path(
        "congress/event/change-entry/<int:congress_id>/<int:event_id>",
        views.edit_event_entry,
        name="edit_event_entry",
    ),
    #    path("congress/edit/<int:congress_id>", views.edit_congress, name="edit_congress"),
    path(
        "congress/delete/<int:congress_id>",
        views.delete_congress,
        name="delete_congress",
    ),
    #    path("congress/create2", views.create_congress, name="create_congress"),
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
        ajax.get_conveners_ajax,
        name="get_conveners_ajax",
    ),
    path(
        "congress/create/get-congress-master/<int:org_id>",
        ajax.get_congress_master_ajax,
        name="get_congress_master_ajax",
    ),
    path(
        "congress/create/get-congress/<int:congress_id>",
        ajax.get_congress_ajax,
        name="get_congress_ajax",
    ),
    path(
        "congress/create/add-event/<int:congress_id>",
        views.create_event,
        name="create_event",
    ),
    path(
        "congress/create/edit-event/<int:congress_id>/<int:event_id>",
        views.edit_event,
        name="edit_event",
    ),
    path(
        "congress/create/add-session/<int:event_id>",
        views.create_session,
        name="create_session",
    ),
    path(
        "congress/admin/summary/<int:congress_id>",
        views.admin_summary,
        name="admin_summary",
    ),
    path("congress/checkout", views.checkout, name="checkout",),
    path("congress/checkout<int:congress_id>", views.checkout, name="checkout",),
    path(
        "congress/create/edit-session/<int:event_id>/<int:session_id>",
        views.edit_session,
        name="edit_session",
    ),
    path(
        "congress/create/delete-event",
        ajax.delete_event_ajax,
        name="delete_event_ajax",
    ),
    path(
        "congress/create/delete-session",
        ajax.delete_session_ajax,
        name="delete_session_ajax",
    ),
    path(
        "congress/event/enter/fee-for-user",
        ajax.fee_for_user_ajax,
        name="fee_for_user_ajax",
    ),
    path(
        "congress/event/enter/payment-options-for-user",
        ajax.payment_options_for_user_ajax,
        name="payment_options_for_user_ajax",
    ),
]
