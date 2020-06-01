from django.shortcuts import render
from .models import RBACGroup, RBACUserGroup, RBACGroupRole

def rbac_create_group(group_name):
    """ Create an RBAC group

    Args:
        user(User): user making change
        group_name(str): name of group to create

    Returns:
        RBACGroup
    """

    obj = RBACGroup(group_name=group_name)
    obj.save()
    return obj

def rbac_delete_group(group):
    """ Delete an RBAC group

    Args:
        group(RBACGroup): id of group to delete

    Returns:
        Nothing
    """

    group.delete()

def rbac_delete_group_by_name(group_name):
    """ Delete an RBAC group by name

    Args:
        group_name(str): group name to delete

    Returns:
        Nothing
    """

    group = RBACGroup.objects.get(group_name=group_name)
    group.delete()


def rbac_add_user_to_group(member, group):
    """ Adds a user to an RBAC group

    Args:
        member(User): standard user object
        group(RBACGroup): group to add to
    """

    return True

def rbac_remove_user_from_group(member, group):
    """ Removes a user from an RBAC group

    Args:
        member(User): standard user object
        group(RBACGroup): group to remove user from

    Returns:
        Nothing
    """

    return True

def rbac_add_role_to_group(group, role):
    """ Adds a user to an RBAC group

    Args:
        group(RBACGroup): group
        role(str): role to add to group

    Returns:
        Nothing
    """

    return True

def rbac_remove_role_from_group(group, role):
    """ Removes a user from an RBAC group

    Args:
        group(RBACGroup): group
        role(str): role to remove from group

    Returns:
        Nothing
    """

    return True

def user_has_role(member, role):
    """ check if a user has a specific role

    Args:
        member(User): standard user object
        role(str):  role to check

    Returns:
        bool: True of False for user role
    """

    return False
