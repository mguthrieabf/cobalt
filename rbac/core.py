""" Role Based Access Control Core

    This handles the core functions for role based security for Cobalt.

    See `RBAC Overview`_ for more details.

    .. _RBAC Overview:
       ./rbac_overview.html
"""
from .models import (
    RBACGroup,
    RBACUserGroup,
    RBACGroupRole,
    RBACAdminUserGroup,
    RBACAdminGroupRole,
    RBACModelDefault,
)
from cobalt.settings import RBAC_EVERYONE


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
    except RBACGroup.DoesNotExist:
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
    except RBACGroup.DoesNotExist:
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
    except RBACUserGroup.DoesNotExist:
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
    except RBACGroupRole.DoesNotExist:
        return False


def rbac_user_has_role(member, role):
    """ check if a user has a specific role

    Args:
        member(User): standard user object
        role(str): role to check

    Returns:
        bool: True of False for user role
    """
    print("-->user_has_role: User is: %s. Role is: %s" % (member.full_name, role))
    # breakdown role into parts
    (app, model, model_instance, action) = role_to_parts(role)
    # we also match against an action of all. e.g. if the role is:
    #  forums.forum.5.create then we will also accept finding:
    #  forums.forum.5.all.
    if model_instance:
        all_role = "%s.%s.%s.all" % (app, model, model_instance)
    else:
        all_role = "%s.%s.all" % (app, model)

    groups = RBACUserGroup.objects.filter(
        member__in=[member, RBAC_EVERYONE]
    ).values_list("group")
    print("-->user_has_role: Looked up groups for %s:" % member)
    for g in groups:
        print("  -->>user_has_group: Found %s" % g)
    matches = RBACGroupRole.objects.filter(group__in=groups)
    print("-->user_has_role: Looked up roles for groups:")
    for m in matches:
        print("  -->user_has_role: %s" % m)

    # look for specific rule
    for m in matches:
        print("-->user_has_role: role is: %s" % role)
        print("-->user_has_role: Checking %s" % m.role)
        if m.role == role or m.role == all_role:
            print("  -->user_has_role: Matched with %s" % m)
            if m.rule_type == "Allow":
                print("-->user_has_role: Rule is allow - return True")
                return True
            else:
                print("-->user_has_role: Rule is block - return False")
                return False

    # look for general rule
    print("-->user_has_role: No specific match found, next try general")
    print("-->user_has_role: General")
    for m in matches:
        print("-->user_has_role: role is: %s" % role)
        print("-->user_has_role: Checking: %s" % m.role)
        if m.role == "%s.%s.%s" % (app, model, action) or m.role == "%s.%s.all" % (
            app,
            model,
        ):
            print("-->user_has_role: Matched with %s" % m)
            if m.rule_type == "Allow":
                print("-->user_has_role: Rule is allow - return True")
                return True
            else:
                print("-->user_has_role: Rule is block - return False")
                return False

    # No match - use default
    print("-->user_has_role: No general match found, using app.model default")
    default = (
        RBACModelDefault.objects.filter(app=app, model=model)
        .values_list("default_behaviour")
        .first()[0]
    )
    print("-->user_has_role: Default for %s.%s is %s" % (app, model, default))
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
    print(
        "--> user_blocked_for_model: User: %s App: %s Model: %s Action: %s"
        % (user, app, model, action)
    )

    default = RBACModelDefault.objects.filter(app=app, model=model).first()

    if not default:
        raise ReferenceError("%s.%s not set up in RBACModelDefault" % (app, model))

    if default.default_behaviour == "Block":
        raise ReferenceError("Only supported for default Allow models")

    groups = RBACUserGroup.objects.filter(
        member__in=[user.id, RBAC_EVERYONE]
    ).values_list("group")
    print("--> user_blocked_for_model: Looked up groups for %s:" % user)
    for g in groups:
        print("  --> user_blocked_for_model: %s" % g)
    matches = RBACGroupRole.objects.filter(
        group__in=groups, rule_type="Block", action=action
    ).values_list("model_id")
    print("--> user_blocked_for_model: Looked up roles for groups:")
    ret = []
    for m in matches:
        ret.append(m[0])
        print("--> user_blocked_for_model: returning %s" % ret)
    return ret


def rbac_user_allowed_for_model(user, app, model, action):
    """ returns a list of model instances which the user can view

    Args:
        user(User): standard user object
        app(str):   application name
        model(str): model name
        action(str):    action required

    Returns:
        list:   list of model_instances explicitly allowed
    """
    print(
        "--> user_allowed_for_model: User: %s App: %s Model: %s Action: %s"
        % (user, app, model, action)
    )

    default = RBACModelDefault.objects.filter(app=app, model=model).first()

    if not default:
        raise ReferenceError("%s.%s not set up in RBACModelDefault" % (app, model))

    if default.default_behaviour == "Allow":
        raise ReferenceError("Only supported for default Block models")

    groups = RBACUserGroup.objects.filter(
        member__in=[user.id, RBAC_EVERYONE]
    ).values_list("group")
    print("--> user_allowed_for_model: Looked up groups for %s:" % user)
    for g in groups:
        print("  --> user_allowed_for_model: %s" % g)
    matches = RBACGroupRole.objects.filter(
        group__in=groups, rule_type="Allow", action=action
    ).values_list("model_id")
    print("--> user_allowed_for_model: Looked up roles for groups:")
    ret = []
    for m in matches:
        ret.append(m[0])
        print("--> user_allowed_for_model: returning %s" % ret)
    return ret


def rbac_user_is_group_admin(member, group):
    """ check if a user has admin rights to a group.

    If a user has admin access for any of the roles in a group then they can
    change the group membership. That is what this checks for. It doesn't report
    which role allows this, only whether it is allowed or not.

    Args:
        member(User): standard user object
        group(RBACGroup): group to check

    Returns:
        bool: True of False for user role
    """
    print("-->admin_has_role: User is: %s. Group is: %s" % (member.full_name, group))

    matches = RBACGroupRole.objects.filter(group=group)
    print("-->admin_has_role: Looked up roles for group:")
    for m in matches:
        print("  -->admin_has_role: %s" % m)

    for m in matches:
        print("-->admin_has_role: group is: %s" % group)
        print("-->admin_has_role: Checking %s" % m.role)

        if rbac_user_is_role_admin(member, m.role):
            print("  -->admin_has_role: Matched with %s" % m)
            print("-->admin_has_role: - return True")
            return True

    # No match - return False
    return False


def rbac_user_is_role_admin(member, role):
    """ check if a user is an admin for a specific role

    Args:
        member(User): standard user object
        role(str): role to check

    Returns:
        bool: True of False for user role
    """
    print("-->user_is_role_admin: User is: %s. Role is: %s" % (member.full_name, role))
    # breakdown role into parts
    #    (app, model, model_instance, action) = role_to_parts(role)

    # Remove action from role: e.g. org.org.15.create --> org.org.15
    parts = role.split(".")
    role = ".".join(parts[:-1])

    groups = RBACAdminUserGroup.objects.filter(member=member).values_list("group")
    print("-->user_is_role_admin: Looked up admin groups for %s:" % member)
    for g in groups:
        print("  -->>user_is_role_admin: Found %s" % g)
    matches = RBACAdminGroupRole.objects.filter(group__in=groups)
    print("-->user_is_role_admin: Looked up roles for groups:")
    for m in matches:
        print("  -->user_is_role_admin: %s" % m)

    # look for specific rule
    for m in matches:
        print("-->user_is_role_admin: role is: %s" % role)
        print("-->user_is_role_admin: Checking %s" % m.role)
        if "%s.%s.%s" % (m.app, m.model, m.model_id) == role:
            print("  -->user_is_role_admin: Matched with %s" % m)
            return True

    # look for general rule
    print("-->user_is_role_admin: No specific match found, next try general")
    print("-->user_is_role_admin: General")
    for m in matches:
        print("-->user_is_role_admin: role is: %s" % role)
        print("-->user_is_role_admin: Checking: %s" % m.role)
        if m.role == role:
            print("-->user_is_role_admin: Matched with %s" % m)
            return True
    # No match
    return False


def rbac_access_in_english(user):
    """ returns what access a user has in plain English

    Args:
        user(User): a standard User object

    Returns:
        list: list of strings with user access explained
    """

    groups = RBACUserGroup.objects.filter(member=user).values_list("group")
    roles = RBACGroupRole.objects.filter(group__in=groups)
    english = []
    for role in roles:

        if role.rule_type == "Allow":
            verb = "can"
        else:
            verb = "cannot"

        if role.action == "all":
            action_word = "do everything"
        else:
            action_word = role.action

        if role.model_id:
            desc = f"{user.first_name} {verb} {action_word} in {role.model} no. {role.model_id} in the application '{role.app}'."
        else:
            desc = f"{user.first_name} {verb} {action_word} in every {role.model} in the application '{role.app}'."

        english.append(desc)

    return english
