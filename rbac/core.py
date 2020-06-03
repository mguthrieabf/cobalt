""" Role Based Access Control Core

    This handles the core functions for role based security for Cobalt.

    See `RBAC Overview`_ for more details.

    .. _RBAC Overview:
       ./rbac_overview.html
"""
from .models import RBACGroup, RBACUserGroup, RBACGroupRole, RBACModelDefault

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
        group(RBACGroup): Group to delete

    Returns:
        bool
    """

    try:
        group.delete()
        return True
    except DoesNotExist:
        return False

def rbac_delete_group_by_name(group_name):
    """ Delete an RBAC group by name

    Args:
        group_name(str): group name to delete

    Returns:
        bool
    """

    try:
        group = RBACGroup.objects.get(group_name=group_name)
        group.delete()
        return True
    except DoesNotExist:
        return False

def rbac_add_user_to_group(member, group):
    """ Adds a user to an RBAC group

    Args:
        member(User): standard user object
        group(RBACGroup): group to add to

    Returns:
        RBACUserGroup
    """

    user_group = RBACUserGroup(member=member, group=group)
    user_group.save()
    return user_group

def rbac_remove_user_from_group(member, group):
    """ Removes a user from an RBAC group

    Args:
        member(User): standard user object
        group(RBACGroup): group to remove user from

    Returns:
        bool
    """

    try:
        user_group = RBACUserGroup.objects.filter(member=member, group=group)
        user_group.delete()
        return True
    except DoesNotExist:
        return False

def rbac_add_role_to_group(group, role):
    """ Adds a user to an RBAC group

    Args:
        group(RBACGroup): group
        role(str): role to add to group

    Returns:
        RBACGroupRole
    """

    group_role = RBACGroupRole(group=group, role=role)
    group_role.save()

    return group_role

def rbac_remove_role_from_group(group, role):
    """ Removes a user from an RBAC group

    Args:
        group(RBACGroup): group
        role(str): role to remove from group

    Returns:
        bool
    """

    try:
        group_role = RBACGroupRole.objects.filter(group=group, role=role)
        group_role.delete()
        return True
    except DoesNotExist:
        return False

def user_has_role(member, role):
    """ check if a user has a specific role

    Args:
        member(User): standard user object
        role(str): role to check

    Returns:
        bool: True of False for user role
    """

# breakdown role into parts
    (app, model, model_instance, action) = role_to_parts(role)

    groups = RBACUserGroup.objects.filter(member=member).values_list('group')
    print("Looked up groups for %s:" % member)
    for g in groups:
        print(g)
    matches = RBACGroupRole.objects.filter(group__in=groups)
    print("Looked up roles for groups:")
    for m in matches:
        print(m)

# look for specific rule
    for m in matches:
        print("rol is   #%s#" % role)
        print("Checking #%s#" % m.role)
        if m.role == role:
            print ("Matched with %s" % m)
            if m.rule_type == "Allow":
                print("Rule is allow - return True")
                return True
            else:
                print("Rule is block - return False")
                return False

# look for general rule
    print("General")
    for m in matches:
        print("rol is   #%s#" % role)
        print("Checking #%s#" % m.role)
        if m.role == "%s.%s.%s" % (app, model, action):
            print ("Matched with %s" % m)
            if m.rule_type == "Allow":
                print("Rule is allow - return True")
                return True
            else:
                print("Rule is block - return False")
                return False

    return True

def role_to_parts(role):
    """ take a role string and return it in parts
    Args:
        role(str):  string in format e.g. forums.forum.5.view

    Returns:
        tuple:  (app, model, model_instance, action)
    """

    parts = role.split(".")
    app = parts[0]
    model = parts[1]
    action = parts[-1]

    if len(parts) == 4:
        model_instance = parts[2]
    else:
        model_instance = None

    print("app: %s" % app)
    print("model: %s" % model)
    print("model instance: %s" % model_instance)
    print("action: %s" % action)

    return (app, model, model_instance, action)

def rbac_user_blocked_for_model(user, app, model, action):
    """ returns a list of model instances which the user cannot view
    Args:
        user(User): standard user object
        app(str):   application name
        model(str): model name
        action(str):    action required

    Returns:
        list:   list of model_instances explicitly block
    """

    default = RBACModelDefault.objects.filter(app=app, model=model).first()

    if not default:
        raise ReferenceError("%s.%s not set up in RBACModelDefault" % (app, model))

    if default.default_behaviour == "Block":
        raise ReferenceError("Only supported for default Allow models")

    groups = RBACUserGroup.objects.filter(member__in=[user.id, 1]).values_list('group')
    print("Looked up groups for %s:" % user)
    for g in groups:
        print(g)
    matches = RBACGroupRole.objects.filter(group__in=groups, rule_type="Block", action=action).values_list("model_id")
    print("Looked up roles for groups:")
    ret = []
    for m in matches:
        ret.append(m[0])
    return ret
