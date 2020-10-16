from django.urls import path, include
from . import views, ajax, congress_builder, congress_admin

app_name = "events"  # pylint: disable=invalid-name

urlpatterns = [
    # path("congress-builder", include("events.urls_congress_builder", namespace="congress_builder")),
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
        "congress/event/enter/success",
        views.enter_event_success,
        name="enter_event_success",
    ),
    path(
        "congress/event/view-event-entries/<int:congress_id>/<int:event_id>",
        views.view_event_entries,
        name="view_event_entries",
    ),
    path(
        "congress/event/change-entry/<int:congress_id>/<int:event_id>",
        views.edit_event_entry,
        name="edit_event_entry",
    ),
    path(
        "congress/delete/<int:congress_id>",
        congress_builder.delete_congress,
        name="delete_congress",
    ),
    path(
        "congress/create/wizard",
        congress_builder.create_congress_wizard,
        name="create_congress_wizard",
    ),
    path(
        "congress/create/wizard/<int:step>",
        congress_builder.create_congress_wizard,
        name="create_congress_wizard",
    ),
    path(
        "congress/create/wizard/<int:congress_id>/<int:step>",
        congress_builder.create_congress_wizard,
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
        congress_builder.create_event,
        name="create_event",
    ),
    path(
        "congress/create/edit-event/<int:congress_id>/<int:event_id>",
        congress_builder.edit_event,
        name="edit_event",
    ),
    path(
        "congress/create/add-session/<int:event_id>",
        congress_builder.create_session,
        name="create_session",
    ),
    path(
        "congress/admin/summary/<int:congress_id>",
        congress_admin.admin_summary,
        name="admin_summary",
    ),
    path(
        "congress/admin/summary/event/<int:event_id>",
        congress_admin.admin_event_summary,
        name="admin_event_summary",
    ),
    path(
        "congress/admin/detail/event-entry/<int:evententry_id>",
        congress_admin.admin_evententry,
        name="admin_evententry",
    ),
    path(
        "congress/admin/detail/event-entry-delete/<int:evententry_id>",
        congress_admin.admin_evententry_delete,
        name="admin_evententry_delete",
    ),
    path(
        "congress/admin/detail/event-entry-player/<int:evententryplayer_id>",
        congress_admin.admin_evententryplayer,
        name="admin_evententryplayer",
    ),
    path(
        "congress/admin/event-csv/<int:event_id>",
        congress_admin.admin_event_csv,
        name="admin_event_csv",
    ),
    path(
        "congress/admin/event-log/<int:event_id>",
        congress_admin.admin_event_log,
        name="admin_event_log",
    ),
    path(
        "congress/admin/event-offsystem/<int:event_id>",
        congress_admin.admin_event_offsystem,
        name="admin_event_offsystem",
    ),
    path("congress/checkout", views.checkout, name="checkout",),
    path(
        "congress/create/edit-session/<int:event_id>/<int:session_id>",
        congress_builder.edit_session,
        name="edit_session",
    ),
    path("congress/teammate/checkout", views.pay_outstanding, name="pay_outstanding"),
    path(
        "congress/create/delete-event",
        ajax.delete_event_ajax,
        name="delete_event_ajax",
    ),
    path(
        "congress/create/delete-category",
        ajax.delete_category_ajax,
        name="delete_category_ajax",
    ),
    path(
        "congress/create/delete-session",
        ajax.delete_session_ajax,
        name="delete_session_ajax",
    ),
    path(
        "congress/create/add-category",
        ajax.add_category_ajax,
        name="add_category_ajax",
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
    path(
        "congress/admin/off-system/pay",
        ajax.admin_offsystem_pay_ajax,
        name="admin_offsystem_pay_ajax",
    ),
    path("view", views.view_events, name="view_events",),
]
