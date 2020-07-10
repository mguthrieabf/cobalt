from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import (
    RBACGroup,
    RBACUserGroup,
    RBACGroupRole,
    RBACAdminUserGroup,
    RBACAdminGroup,
    RBACAdminGroupRole,
    RBACAdminTree,
)
from .core import (
    rbac_add_user_to_group,
    rbac_user_is_group_admin,
    rbac_access_in_english,
    rbac_admin_all_rights,
    rbac_get_admins_for_group,
    rbac_user_role_list,
    rbac_user_has_role,
    rbac_get_groups_for_role,
)
from .forms import AddGroup
from django.contrib import messages
from organisations.models import Organisation


@login_required
def rbac_forbidden(request, role):
    """ RBAC screen for fobidden access - gives the user more info than a
    normal error screen """

    groups = rbac_get_groups_for_role(role)

    return render(request, "rbac/forbidden.html", {"role": role, "groups": groups})


@login_required
def main_admin_screen(request):
    """ Shows the main admin screen - maybe shouldn't live in in RBAC """

    payments_admin = rbac_user_role_list(request.user, "payments", "manage")
    org_list = []
    for item in payments_admin:
        org_list.append(item[0])

    orgs = Organisation.objects.filter(pk__in=org_list)

    payments_site_admin = rbac_user_has_role(request.user, "payments.global.view")

    return render(
        request,
        "rbac/main-admin-screen.html",
        {"payments_admin": orgs, "payments_site_admin": payments_site_admin},
    )


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

    group_list = user_groups.values_list("group")
    roles = RBACGroupRole.objects.filter(group__in=group_list)

    english = rbac_access_in_english(request.user)

    return render(
        request,
        "rbac/view-screen.html",
        {"groups": data, "english": english, "roles": roles},
    )


# @login_required
# def admin_screen(request):
#     """ Allows an administrator to control who is in a group and to create
#     roles """
#
#     user_groups = RBACAdminUserGroup.objects.filter(member=request.user)
#
#     # split by type
#     data = {}
#     for user_group in user_groups:
#         if user_group.group.name_qualifier in data:
#             data[user_group.group.name_qualifier].append(user_group.group)
#         else:
#             data[user_group.group.name_qualifier] = [user_group.group]
#     print(user_groups)
#     print(data)
#
#     return render(request, "rbac/admin-screen.html", {"groups": data})


@login_required
def tree_screen(request):
    """ Show full RBAC Tree """
    # Get groups
    groups = RBACGroup.objects.all().order_by("name_qualifier")

    return render(request, "rbac/tree-screen.html", {"groups": groups})


@login_required
def admin_tree_screen(request):
    """ Show full RBAC Admin Tree """
    # Get groups
    groups = RBACAdminGroup.objects.all().order_by("name_qualifier")

    return render(request, "rbac/admin-tree-screen.html", {"groups": groups})


@login_required
def group_view(request, group_id):
    """ view to show details of a group """

    group = get_object_or_404(RBACGroup, pk=group_id)
    users = RBACUserGroup.objects.filter(group=group)
    roles = RBACGroupRole.objects.filter(group=group)
    is_admin = rbac_user_is_group_admin(request.user, group)
    admins = rbac_get_admins_for_group(group)
    return render(
        request,
        "rbac/group_view.html",
        {
            "users": users,
            "roles": roles,
            "group": group,
            "is_admin": is_admin,
            "admins": admins,
        },
    )


@login_required
def admin_group_view(request, group_id):
    """ view to show details of an admin group """

    group = get_object_or_404(RBACAdminGroup, pk=group_id)
    users = RBACAdminUserGroup.objects.filter(group=group)
    roles = RBACAdminGroupRole.objects.filter(group=group)
    return render(
        request,
        "rbac/admin_group_view.html",
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
def admin_group_delete(request, group_id):
    """ view to delete an admin group """

    group = get_object_or_404(RBACAdminGroup, pk=group_id)
    if not rbac_user_is_group_admin(request.user, group):
        return HttpResponse("You are not an admin for this group")
    else:
        if request.method == "POST":
            group.delete()
            messages.success(
                request,
                "Admin Group successfully deleted.",
                extra_tags="cobalt-message-success",
            )
            return redirect("rbac:access_screen")
        return render(request, "rbac/admin_group_delete.html", {"group": group})


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
            return redirect("rbac:group_edit", group_id=group.id)

    else:
        form = AddGroup(user=request.user)
    return render(request, "rbac/group_create.html", {"form": form})


@login_required
def admin_group_create(request):
    """ view to create a new admin group """

    if request.method == "POST":
        form = AddGroup(request.POST, user=request.user)
        if form.is_valid():
            group = RBACAdminGroup(
                name_item=form.cleaned_data["name_item"],
                name_qualifier=form.cleaned_data["name_qualifier"],
                description=form.cleaned_data["description"],
                created_by=request.user,
            )
            group.save()
            messages.success(
                request,
                "Admin Group successfully created.",
                extra_tags="cobalt-message-success",
            )
            if form.cleaned_data["add_self"]:
                mapping = RBACAdminUserGroup(group=group, member=request.user)
                mapping.save()
                messages.success(
                    request,
                    "Added you to group %s." % group,
                    extra_tags="cobalt-message-success",
                )
            return redirect("rbac:rbac_admin")

    else:
        form = AddGroup(user=request.user)
    return render(request, "rbac/admin_group_create.html", {"form": form})


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
def rbac_admin(request):
    """ shows the admin groups a user is in """

    group_list = RBACAdminUserGroup.objects.filter(member=request.user).values_list(
        "group"
    )
    groups = RBACAdminGroup.objects.filter(id__in=group_list)

    roles = RBACAdminGroupRole.objects.filter(group__in=group_list)

    group_list = RBACAdminUserGroup.objects.filter(member=request.user).values_list(
        "group"
    )
    trees = RBACAdminTree.objects.filter(group__in=group_list)

    return render(
        request,
        "rbac/admin-screen.html",
        {"groups": groups, "roles": roles, "trees": trees},
    )
