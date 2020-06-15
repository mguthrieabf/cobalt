from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from .models import (
    RBACGroup,
    RBACUserGroup,
    RBACGroupRole,
    RBACAdminUserGroup,
    RBACAppModelAction,
)
from .core import (
    rbac_add_user_to_group,
    rbac_user_is_group_admin,
    rbac_access_in_english,
    rbac_remove_user_from_group,
    rbac_admin_all_rights,
    rbac_user_is_role_admin,
    rbac_add_role_to_group,
)
from accounts.models import User
from .forms import AddGroup
from django.contrib import messages


@login_required
def view_screen(request):
    """ Shows the user what roles they have in RBAC """

    user_groups = RBACUserGroup.objects.filter(member=request.user)

    # split by type
    data = {}
    for user_group in user_groups:
        if user_group.group.name_qualifier in data:
            data[user_group.group.name_qualifier].append(user_group.group)
        else:
            data[user_group.group.name_qualifier] = [user_group.group]

    english = rbac_access_in_english(request.user)

    return render(
        request, "rbac/view-screen.html", {"groups": data, "english": english}
    )


@login_required
def admin_screen(request):
    """ Allows an administrator to control who is in a group and to create
    roles """

    user_groups = RBACAdminUserGroup.objects.filter(member=request.user)

    # split by type
    data = {}
    for user_group in user_groups:
        if user_group.group.name_qualifier in data:
            data[user_group.group.name_qualifier].append(user_group.group)
        else:
            data[user_group.group.name_qualifier] = [user_group.group]
    print(user_groups)
    print(data)

    return render(request, "rbac/admin-screen.html", {"groups": data})


@login_required
def tree_screen(request):
    """ Show full RBAC Tree """
    # Get groups
    groups = RBACGroup.objects.all().order_by("name_qualifier")

    return render(request, "rbac/tree-screen.html", {"groups": groups})


@login_required
def group_view(request, group_id):
    """ view to show details of a group """

    group = get_object_or_404(RBACGroup, pk=group_id)
    users = RBACUserGroup.objects.filter(group=group)
    roles = RBACGroupRole.objects.filter(group=group)
    return render(
        request,
        "rbac/group_view.html",
        {"users": users, "roles": roles, "group": group},
    )


@login_required
def group_delete(request, group_id):
    """ view to delete a group """

    group = get_object_or_404(RBACGroup, pk=group_id)
    if not rbac_user_is_group_admin(request.user, group):
        return HttpResponse("You are not an admin for this group")
    else:
        if request.method == "POST":
            group.delete()
            messages.success(
                request,
                "Group successfully deleted.",
                extra_tags="cobalt-message-success",
            )
            return redirect("rbac:access_screen")
        return render(request, "rbac/group_delete.html", {"group": group})


@login_required
def group_create(request):
    """ view to create a new group """

    if request.method == "POST":
        form = AddGroup(request.POST, user=request.user)
        if form.is_valid():
            group = RBACGroup(
                name_item=form.cleaned_data["name_item"],
                name_qualifier=form.cleaned_data["name_qualifier"],
                description=form.cleaned_data["description"],
                created_by=request.user,
            )
            group.save()
            if form.cleaned_data["add_self"]:
                rbac_add_user_to_group(request.user, group)
            return render(request, "rbac/admin-screen.html")

    else:
        form = AddGroup(user=request.user)
    return render(request, "rbac/group_create.html", {"form": form})


@login_required
def group_edit(request, group_id):
    """ view to edit a group """

    group = get_object_or_404(RBACGroup, pk=group_id)
    if not rbac_user_is_group_admin(request.user, group):
        return HttpResponse("You are not an admin for this group")
    else:
        if request.method == "POST":
            form = AddGroup(request.POST, user=request.user)
            if form.is_valid():
                group.name_item = form.cleaned_data["name_item"]
                group.description = form.cleaned_data["description"]
                group.save()
                messages.success(
                    request,
                    "Group successfully updated.",
                    extra_tags="cobalt-message-success",
                )
            else:
                print(form.errors)
        else:
            form = AddGroup(user=request.user)
            form.fields["name_item"].initial = group.name_item
            form.fields["description"].initial = group.description

        users = RBACUserGroup.objects.filter(group=group)
        admin_roles = rbac_admin_all_rights(request.user)
        roles = RBACGroupRole.objects.filter(group=group)
        print(admin_roles)
        return render(
            request,
            "rbac/group_edit.html",
            {
                "form": form,
                "group": group,
                "users": users,
                "roles": roles,
                "admin_roles": admin_roles,
            },
        )


@login_required
def group_to_user_ajax(request, group_id):
    """ Called by the admin page when a user selects a group.

    Takes the RBACGroup id and return the matching records from RBACUserGroup

    Args:
        request (HTTPRequest): standard request object.
        group_id (int): RBACGroup id to use for queries

    Returns:
        HTTPResponse: Ajax JSON object

    """
    group = RBACGroup.objects.get(pk=group_id)
    usergroups = RBACUserGroup.objects.filter(group=group)

    html = render_to_string(
        template_name="rbac/group-to-user.html", context={"usergroups": usergroups}
    )
    data_dict = {"data": html}
    return JsonResponse(data=data_dict, safe=False)


@login_required
def group_to_action_ajax(request, group_id):
    """ Called by the admin page when a user selects a group.

    Takes the RBACGroup id and return the matching records from RBACGroupRole

    Args:
        request (HTTPRequest): standard request object.
        group_id (int): RBACGroup id to use for queries

    Returns:
        HTTPResponse: Ajax JSON object

    """
    group = RBACGroup.objects.get(pk=group_id)
    roles = RBACGroupRole.objects.filter(group=group)

    html = render_to_string(
        template_name="rbac/group-to-action.html", context={"roles": roles}
    )
    data_dict = {"data": html}
    return JsonResponse(data=data_dict, safe=False)


@login_required()
def rbac_add_user_to_group_ajax(request):
    """ Ajax call to add a user to a group

    Args:
        request(HTTPRequest): standard request

    Returns:
        HTTPResponse: success, failure or error
    """

    if request.method == "GET":
        member_id = request.GET["member_id"]
        group_id = request.GET["group_id"]

        member = User.objects.get(pk=member_id)
        group = RBACGroup.objects.get(pk=group_id)

        if rbac_user_is_group_admin(request.user, group):
            rbac_add_user_to_group(member, group)
            print("User %s added to group %s" % (member, group))
            msg = "Success"
        else:
            print("Access Denied")
            msg = "Access Denied"

    else:
        msg = "Invalid request"

    response_data = {}
    response_data["message"] = msg
    return JsonResponse({"data": response_data})


@login_required()
def rbac_add_role_to_group_ajax(request):
    """ Ajax call to add a role to a group

    Args:
        request(HTTPRequest): standard request

    Returns:
        HTTPResponse: success, failure or error
    """

    if request.method == "GET":
        group_id = request.GET["group_id"]
        app = request.GET["app"]
        model = request.GET["model"]
        model_id = request.GET["model_id"]
        action = request.GET["action"]
        rule_type = request.GET["rule_type"]

        group = RBACGroup.objects.get(pk=group_id)

        role = RBACGroupRole.objects.get(group=group)

        # rbac_user_is_role_admin expects an action at the end of the string
        if role.model_id:
            role_str = "%s.%s.%s.action" % (role.app, role.model, role.model_id)
        else:
            role_str = "%s.%s.action" % (role.app, role.model)

        if rbac_user_is_role_admin(request.user, role_str):

            rbac_add_role_to_group(
                group=group,
                app=app,
                model=model,
                model_id=model_id,
                action=action,
                rule_type=rule_type,
            )
            msg = "Success"
        else:
            print("Access Denied")
            msg = "Access Denied"

    else:
        msg = "Invalid request"

    response_data = {}
    response_data["message"] = msg
    return JsonResponse({"data": response_data})


@login_required()
def rbac_get_action_for_model_ajax(request):
    """ Ajax call to get the action types for a given app and model

    Args:
        request(HTTPRequest): standard request - needs to include "app" and "model"

    Returns:
        HTTPResponse: success, failure or error
    """

    if request.method == "GET":
        app = request.GET["app"]
        model = request.GET["model"]

        actions = RBACAppModelAction.objects.filter(app=app, model=model).values_list(
            "valid_action"
        )
        print(actions)
        print(app)
        print(model)
    else:
        msg = "Invalid request"
        response_data = {}
        response_data["message"] = msg
        return JsonResponse({"data": response_data})

    html = render_to_string(
        template_name="rbac/app-model-actions.html", context={"actions": actions}
    )
    data_dict = {"data": html}
    return JsonResponse(data=data_dict, safe=False)


@login_required()
def rbac_delete_user_from_group_ajax(request):
    """ Ajax call to delete a user from a group

    Args:
        request(HTTPRequest): standard request

    Returns:
        HTTPResponse: success, failure or error
    """

    if request.method == "GET":
        member_id = request.GET["member_id"]
        group_id = request.GET["group_id"]

        member = User.objects.get(pk=member_id)
        group = RBACGroup.objects.get(pk=group_id)

        if rbac_user_is_group_admin(request.user, group):
            rbac_remove_user_from_group(member, group)
            print("User %s delete from group %s" % (member, group))
            msg = "Success"
        else:
            print("Access Denied")
            msg = "Access Denied"

    else:
        msg = "Invalid request"

    response_data = {}
    response_data["message"] = msg
    return JsonResponse({"data": response_data})


@login_required()
def rbac_delete_role_from_group_ajax(request):
    """ Ajax call to delete a role from a group

    Args:
        request(HTTPRequest): standard request

    Returns:
        HTTPResponse: success, failure or error
    """

    if request.method == "GET":
        role_id = request.GET["role_id"]

        role = RBACGroupRole.objects.get(pk=role_id)

        if role.model_id:
            role_str = "%s.%s.%s" % (role.app, role.model, role.model_id)
        else:
            role_str = "%s.%s" % (role.app, role.model)

        if rbac_user_is_role_admin(request.user, role_str):
            role.delete()
            msg = "Success"
        else:
            print("Access Denied")
            msg = "Access Denied"

    else:
        msg = "Invalid request"

    response_data = {}
    response_data["message"] = msg
    return JsonResponse({"data": response_data})
