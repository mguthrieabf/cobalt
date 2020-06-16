# pylint: disable=missing-module-docstring,missing-class-docstring
from django.urls import path
from . import views, ajax

app_name = "rbac"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.view_screen, name="access_screen"),
    # path("admin", views.admin_screen, name="admin_screen"),
    path("mainadmin", views.main_admin_screen, name="main_admin_screen"),
    path("tree", views.tree_screen, name="tree_screen"),
    path("group/view/<int:group_id>/", views.group_view, name="group_view"),
    path("group/edit/<int:group_id>/", views.group_edit, name="group_edit"),
    path("group/delete/<int:group_id>/", views.group_delete, name="group_delete"),
    path("group/create", views.group_create, name="group_create"),
    path("admin", views.rbac_admin, name="rbac_admin"),
    path("admin/tree", views.admin_tree_screen, name="admin_tree_screen"),
    path("admin/group/create", views.admin_group_create, name="admin_group_create"),
    path(
        "admin/group/view/<int:group_id>/",
        views.admin_group_view,
        name="admin_group_view",
    ),
    path(
        "admin/group/delete/<int:group_id>/",
        views.admin_group_delete,
        name="admin_group_delete",
    ),
    path(
        "group/rbac-get-action-for-model-ajax",
        ajax.rbac_get_action_for_model_ajax,
        name="rbac_get_action_for_model_ajax",
    ),
    path(
        "rbac-add-user-to-group-ajax",
        ajax.rbac_add_user_to_group_ajax,
        name="rbac_add_user_to_group_ajax",
    ),
    path(
        "rbac-delete-user-from-group-ajax",
        ajax.rbac_delete_user_from_group_ajax,
        name="rbac_delete_user_from_group_ajax",
    ),
    path(
        "rbac-delete-role-from-group-ajax",
        ajax.rbac_delete_role_from_group_ajax,
        name="rbac_delete_role_from_group_ajax",
    ),
    path(
        "rbac-add-role-to-group-ajax",
        ajax.rbac_add_role_to_group_ajax,
        name="rbac_add_role_to_group_ajax",
    ),
    path(
        "group-to-user/<int:group_id>/",
        ajax.group_to_user_ajax,
        name="group_to_user_ajax",
    ),
    path(
        "group-to-action/<int:group_id>/",
        ajax.group_to_action_ajax,
        name="group_to_action_ajax",
    ),
]
