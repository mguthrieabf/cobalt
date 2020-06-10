from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from .models import (
    RBACGroup,
    RBACUserGroup,
    RBACGroupRole,
    RBACAdminUserGroup,
    RBACAdminGroupRole,
    RBACAdminGroup,
)
from .core import rbac_add_user_to_group, rbac_user_is_group_admin
from accounts.models import User


@login_required
def access_screen(request):

    # TODO: work out how to do this more efficiently using select_related
    # Get groups with this user
    groups1 = RBACUserGroup.objects.filter(member=request.user).values_list("group")

    # Get roles from groups where action is admin
    matches = RBACGroupRole.objects.filter(group__in=groups1).values_list("group")

    # Get groups
    groups = RBACGroup.objects.filter(id__in=matches).order_by("name_qualifier")

    # split by type
    data = {}
    for group in groups:
        if group.group_type in data:
            data[group.group_type].append(group)
        else:
            data[group.group_type] = [group]

    return render(request, "rbac/admin-screen.html", {"groups": data})


@login_required
def admin_screen(request):

    # TODO: work out how to do this more efficiently using select_related
    # Get groups with this user
    groups1 = RBACAdminUserGroup.objects.filter(member=request.user).values_list(
        "group"
    )

    # Get roles from groups where action is admin
    matches = RBACAdminGroupRole.objects.filter(group__in=groups1).values_list("group")

    # Get groups
    groups = RBACAdminGroup.objects.filter(id__in=matches).order_by("name_qualifier")

    # split by type
    data = {}
    for group in groups:
        if group.group_type in data:
            data[group.group_type].append(group)
        else:
            data[group.group_type] = [group]

    return render(request, "rbac/admin-screen.html", {"groups": data})


def all_screen(request):
    """ temp for development purposes """
    # Get groups
    groups = RBACGroup.objects.all().order_by("name_qualifier")

    # split by type
    data = {}
    for group in groups:
        if group.group_type in data:
            data[group.group_type].append(group)
        else:
            data[group.group_type] = [group]

    return render(request, "rbac/admin-screen.html", {"groups": data})


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
