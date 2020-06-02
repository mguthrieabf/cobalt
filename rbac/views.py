from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from .models import RBACGroup, RBACUserGroup, RBACGroupRole

@login_required
def admin_screen(request):

# TODO: work out how to do this more efficiently using select_related
# Get groups with this user
    groups1 = RBACUserGroup.objects.filter(member=request.user).values_list('group')

# Get roles from groups where action is admin
    matches = RBACGroupRole.objects.filter(group__in=groups1, action="admin").values_list('group')

# Get groups
    groups = RBACGroup.objects.filter(id__in=matches).order_by('group_name')

# split by type
    data={}
    for group in groups:
        admin_type = group.group_name.split(".")[0].title()  # forums.1 becomes Forums
        if admin_type in data:
            data[admin_type].append(group)
        else:
            data[admin_type] = [group]


    return render(request, 'rbac/admin-screen.html', {'groups': data})

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
        template_name="rbac/group-to-user.html",
        context={'usergroups': usergroups}
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
        template_name="rbac/group-to-action.html",
        context={'roles': roles}
    )
    data_dict = {"data": html}
    return JsonResponse(data=data_dict, safe=False)
