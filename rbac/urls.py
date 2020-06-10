# pylint: disable=missing-module-docstring,missing-class-docstring
from django.urls import path
from . import views

app_name = "rbac"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.access_screen, name="access_screen"),
    path("admin", views.admin_screen, name="admin_screen"),
    path("all", views.all_screen, name="all_screen"),
    path(
        "rbac-add-user-to-group-ajax",
        views.rbac_add_user_to_group_ajax,
        name="rbac_add_user_to_group_ajax",
    ),
    path(
        "group-to-user/<int:group_id>/",
        views.group_to_user_ajax,
        name="group_to_user_ajax",
    ),
    path(
        "group-to-action/<int:group_id>/",
        views.group_to_action_ajax,
        name="group_to_action_ajax",
    ),
]
