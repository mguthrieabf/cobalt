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
    RBACAdminTree,
)
from cobalt.settings import RBAC_EVERYONE
from accounts.models import User


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


def rbac_add_role_to_group(group, app, model, action, rule_type, model_id=None):

    """ Adds a role to an RBAC group

    Args:
        group(RBACGroup): group
        app(str):   name of the app
        model(str): name of the model
        action(str):    action
        rule_type(str): Allow or Block
        model_id(int):  model instance (Optional)

    Returns:
        RBACGroupRole
    """

    group_role = RBACGroupRole()
    group_role.group = group
    group_role.app = app
    group_role.model = model
    group_role.action = action
    group_role.rule_type = rule_type
    group_role.model_id = model_id
    group_role.save()

    return group_role


#
# def rbac_remove_role_from_group(group, role):
#     """ Removes a role from an RBAC group
#
#     Args:
#         group(RBACGroup): group
#         role(str): role to remove from group
#
#     Returns:
#         bool
#     """
#
#     try:
#         group_role = RBACGroupRole.objects.filter(group=group, role=role)
#         group_role.delete()
#         return True
#     except RBACGroupRole.DoesNotExist:
#         return False


def rbac_user_has_role_exact(member, role):
    """ check if a user has an exact role

    This is called by rbac_user_has_role to check exact roles. The process
    for checking an exact role is always the same. rbac_user_has_role has
    the logic to put this together at a higher level and to use defaults
    in order to work out if the combination of rules allows a user to do
    something. This function only checks at the most specific level.

    Args:
        member(User): standard user object
        role(str): role to check

    Returns:
        string: "Allow", "Block", or None for no match
    """
    (app, model, model_instance, action) = role_to_parts(role)
    # we also match against an action of all. e.g. if the role is:
    #  forums.forum.5.create then we will also accept finding:
    #  forums.forum.5.all.
    if model_instance:
        all_role = "%s.%s.%s.all" % (app, model, model_instance)
    else:
        all_role = "%s.%s.all" % (app, model)

    groups = RBACUserGroup.objects.filter(member=member).values_list("group")
    matches = RBACGroupRole.objects.filter(group__in=groups)

    for m in matches:
        if m.role == role or m.role == all_role:
            return m.rule_type

    # no match
    return None


def rbac_user_has_role(member, role):
    """ check if a user has a specific role

    Args:
        member(User): standard user object
        role(str): role to check

    Returns:
        bool: True or False for user role
    """

    # Is there a specific rule for this user and role
    return_code = rbac_user_has_role_exact(member, role)
    if return_code:
        return allow_to_boolean(return_code)

    # Is there a specific rule for Everyone and this role
    everyone = User.objects.get(pk=RBAC_EVERYONE)
    return_code = rbac_user_has_role_exact(everyone, role)
    if return_code:
        return allow_to_boolean(return_code)

    # Is there a higher role. eg. for forums.forum.5 if no match then is there
    # a rule for forums.forum. We only go one level up for performance reasons.
    if role.count(".") == 2:  # 3 levels
        parts = role.split(".")
        role = ".".join(parts[:2])  # drop last part

        # next level rule for this user
        return_code = rbac_user_has_role_exact(member, role)
        if return_code:
            return allow_to_boolean(return_code)

        #  next level rule for everyone
        return_code = rbac_user_has_role_exact(everyone, role)
        if return_code:
            return allow_to_boolean(return_code)

    # No match or no higher rule - use default
    (app, model, model_instance, action) = role_to_parts(role)
    default = (
        RBACModelDefault.objects.filter(app=app, model=model)
        .values_list("default_behaviour")
        .first()[0]
    )
    return default


def allow_to_boolean(test_string):
    """ takes a string and returns True if it is "Allow" """

    if test_string == "Allow":
        return True
    else:
        return False


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

    # get block rules first for both this user and everyone
    groups = RBACUserGroup.objects.filter(
        member__in=[user.id, RBAC_EVERYONE]
    ).values_list("group")

    everyone_matches = RBACGroupRole.objects.filter(
        group__in=groups, rule_type="Block", action__in=[action, "all"]
    ).values_list("model_id")

    # get rules for this user that allow
    user_groups = RBACUserGroup.objects.filter(member=user).values_list("group")

    user_matches = RBACGroupRole.objects.filter(
        group__in=user_groups, rule_type="Allow", action__in=[action, "all"]
    ).values_list("model_id")

    # allow rules for this user override block rules for everyone
    ret = []
    for m in everyone_matches:
        if m not in user_matches:
            ret.append(m[0])
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

    default = RBACModelDefault.objects.filter(app=app, model=model).first()

    if not default:
        raise ReferenceError("%s.%s not set up in RBACModelDefault" % (app, model))

    if default.default_behaviour == "Allow":
        raise ReferenceError("Only supported for default Block models")

    # get all rules first for both this user and everyone
    groups = RBACUserGroup.objects.filter(
        member__in=[user.id, RBAC_EVERYONE]
    ).values_list("group")

    everyone_matches = RBACGroupRole.objects.filter(
        group__in=groups, rule_type="Allow", action__in=[action, "all"]
    ).values_list("model_id")

    # get rules for this user that block
    user_groups = RBACUserGroup.objects.filter(member=user).values_list("group")

    user_matches = RBACGroupRole.objects.filter(
        group__in=user_groups, rule_type="Block", action__in=[action, "all"]
    ).values_list("model_id")

    # block rules for this user override block rules for everyone
    ret = []
    for m in everyone_matches:
        if m not in user_matches:
            ret.append(m[0])
    return ret


def rbac_admin_all_rights(user):
    """ returns a list of which apps, models and model_ids a user is an admin for

    Args:
        user(User): standard user object

    Returns:
        list:   list of App, model, model_id
    """

    groups = RBACAdminUserGroup.objects.filter(member=user).values_list("group")

    matches = RBACAdminGroupRole.objects.filter(group__in=groups)

    ret = []
    for m in matches:
        if m.model_id:
            ret_str = "%s.%s.%s" % (m.app, m.model, m.model_id)
        else:
            ret_str = "%s.%s" % (m.app, m.model)
        ret.append(ret_str)
    return ret


def rbac_user_is_group_admin(member, group):
    """ check if a user has admin rights to a group based upon their rights
    in the tree. Note - they also need admin rights to the objects if they are
    intending to change the group. This only checks for the ability to change
    group membership or delete the group.

    Args:
        member(User): standard user object
        group(RBACGroup): group to check

    Returns:
        bool: True of False for user role
    """
    print(
        "-->user_is_group_admin: User is: %s. Group is: %s" % (member.full_name, group)
    )

    path = group.name
    print("-->user_is_group_admin: Path is: %s" % path)

    trees = RBACAdminTree.objects.filter(member=member)

    print(
        "-->user_is_group_admin: Count of RBACAdminTree for this user is: %s"
        % trees.count()
    )

    for tree in trees:
        print("-->user_is_group_admin: checking %s = %s" % (tree.tree, path))
        if tree.tree == path:
            print("-->user_is_group_admin: Matched %s = %s" % (tree.tree, path))
            print("-->user_is_group_admin: returning true")
            return True
        # check for match on aaaaa.bbbbb.
        partial = tree.tree + "."
        print("-->user_is_group_admin: checking patial match %s = %s" % (partial, path))
        if path.find(partial) == 0:
            print("-->user_is_group_admin: returning true")
            return True

    return False


def rbac_user_is_role_admin(member, role):
    """ check if a user is an admin for a specific role

    Args:
        member(User): standard user object
        role(str): role to check. should be from role.path e.g. forums.forum.3. No action in string.

    Returns:
        bool: True of False for user role
    """

    print("-->user_is_role_admin: User is: %s. Role is: %s" % (member.full_name, role))

    groups = RBACAdminUserGroup.objects.filter(member=member).values_list("group")
    print("-->user_is_role_admin: Looked up admin groups for %s:" % member)
    print("  -->>user_is_role_admin: Found %s" % groups)
    matches = RBACAdminGroupRole.objects.filter(group__in=groups)
    print("-->user_is_role_admin: Looked up roles for groups:")
    for m in matches:
        print("  -->user_is_role_admin: %s" % m)

    # look for specific rule
    for m in matches:
        # compare strings not objects
        role_str = "%s" % role
        if m.model_id:
            m_str = "%s.%s.%s" % (m.app, m.model, m.model_id)
        else:
            m_str = "%s.%s" % (m.app, m.model)
        print("-->user_is_role_admin: role is: #%s#" % role_str)
        print("-->user_is_role_admin: Checking #%s#" % m_str)
        if m_str == role_str:
            print("  -->user_is_role_admin: Matched with %s" % m)
            return True

    # change role org.org.15 --> org.org
    parts = role.split(".")
    if len(parts) == 3:
        role = ".".join(parts[:-1])

        # look for general rule
        print("-->user_is_role_admin: No specific match found, next try general")
        print("-->user_is_role_admin: General")
        for m in matches:
            # compare strings not objects
            role_str = "%s" % role
            m_str = "%s.%s" % (m.app, m.model)
            print("-->user_is_role_admin: role is: #%s#" % role_str)
            print("-->user_is_role_admin: Checking #%s#" % m_str)

            if m_str == role_str:
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

    return rbac_access_in_english_sub(
        RBAC_EVERYONE, "Everyone"
    ) + rbac_access_in_english_sub(user, user.first_name)


def rbac_access_in_english_sub(user, this_name):
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
            desc = f"{this_name} {verb} {action_word} in {role.model} no. {role.model_id} in the application '{role.app}'."
        else:
            desc = f"{this_name} {verb} {action_word} in every {role.model} in the application '{role.app}'."

        english.append(desc)

    return english


def rbac_get_admins_for_group(group):
    """ returns a queryset of admins for a given group """

    path = group.name
    print(path)
    trees = RBACAdminTree.objects.filter(tree=path)
    print(trees)
    return trees
