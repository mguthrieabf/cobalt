# pylint: disable=missing-module-docstring,missing-class-docstring
from django.urls import path
from . import views

app_name = "rbac"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.view_screen, name="access_screen"),
    path("admin", views.admin_screen, name="admin_screen"),
    path("tree", views.tree_screen, name="tree_screen"),
    path("group/view/<int:group_id>/", views.group_view, name="group_view"),
    path("group/edit/<int:group_id>/", views.group_edit, name="group_edit"),
    path("group/delete/<int:group_id>/", views.group_delete, name="group_delete"),
    path("group/create", views.group_create, name="group_create"),
    path(
        "group/rbac-get-action-for-model-ajax",
        views.rbac_get_action_for_model_ajax,
        name="rbac_get_action_for_model_ajax",
    ),
    path(
        "rbac-add-user-to-group-ajax",
        views.rbac_add_user_to_group_ajax,
        name="rbac_add_user_to_group_ajax",
    ),
    path(
        "rbac-delete-user-from-group-ajax",
        views.rbac_delete_user_from_group_ajax,
        name="rbac_delete_user_from_group_ajax",
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
