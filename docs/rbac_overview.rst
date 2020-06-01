.. _notifications-overview:


.. image:: images/cobalt.jpg
 :width: 300
 :alt: Cobalt Chemical Symbol

RBAC Overview
=============

Role Based Access Control (**RBAC**) is a standard approach to security within
applications that have multiple users with different roles. This allows us to
control a user being an administrator at Club A, a director at Club B, and
a simple member of Club C. It allows us to define moderators for Forums at the
individual forum level rather than having a binary control of being a moderator
or not being a moderator that applies for all forums.

One of the key features of RBAC is the use of Groups to define the level of
access and to encourage users never being given direct security access, but
rather being part of a group that has that access. This makes it easy to give
a new user "Fred" access to the same stuff as "Bob" for his job at Club A
without accidentally also giving him Bob's special access at Club B that he
shouldn't have.

Security Basics
===============

There are two main things when it comes to user security:

  - **Authentication** - Is it you? Userids, passwords, two factor authentication
    etc. Things that let us check it is really you.
  - **Authorisation** - Ok, it is you, but what are you allowed to do?

The RBAC module is about **Authorisation**. It has nothing to do with checking
who you are, just what you can do.

Background
==========

Django Options
--------------

*Django already provides this, so why are we not using that here?*

Django only provides authorisation at a relatively high level.

Basically, with Django, we can control if someone should be able to create
a forum post,
delete a forum post, etc but not which forums they can do this in. We need
our security to be at the next level down, which Django doesn't support.

Third Party Options
-------------------

Short answer, couldn't find one that works, is supported and isn't massively
more complicated to learn than writing our own. The code here is not difficult so
if a better third part option appears then we should use it.

RBAC Roles
==========

When you interact with RBAC you either create, delete or check upon the roles that a
user has. Roles are simple strings, with a role_type of either "Allow" or
"Block". The strings are arbitrary but important to get right if you want the
security to work.

**Format:**

.. code-block:: python

  <app><model>.<optional model_id>.<action>

For example:

1. forums.forum.moderate "Allow"
2. forums.post.5.edit "Block"
3. organisations.organisation.7.admin "Allow"

Example 1 says that this user is allowed to moderate all forums (RBAC doesn't know
what moderating is, it just handles the rules, it is up to each application
to implement the required controls itself). We can break this down as follows:

- *forums* - the Django application in question
- *forum* - the model within the application that this applies to
- *moderate* - the action

Note that an application can choose to use this structure for anything, it doesn't
have to refer to a model, or even an application.

Example 2 is more specific. It says that this user cannot edit the post with a
primary key of 5. This relies on the fact that Django primary keys are unique and
never reused.

**Specific rules take precedent over general rules**

If there are two rules in place as follows:

.. code-block:: python

  payments.stripetransaction.view "Allow"
  payments.stripetransaction.27.view "Block"

Then a request for *payments.stripetransaction.27.view* will return Block.

**Allow is the default behaviour. If no match is found then Allow will be returned**

Groups
======

Roles are never granted to users, they are only granted to Groups and users
can be members of Groups.

API Functions
=============

Mostly, granting access is done by administrators of various levels through
the user interface, so checking access is the most common function.

Note - there is no validation through the API that this action is allowed.
The calling application is responsible for checking this.

Checking User Access
--------------------

To check access you can use the following:

.. code-block:: python

  from rbac.views import rbac_user_has_role

  forum = 6
  if rbac.user_has_role(f"forums.forum.{{forum}}.create"):
    # allow user to continue
  else:
    # show user an error screen

Creating A Group
----------------

To create a group through the API:

.. code-block:: python

  from rbac.views import rbac_create_group

  id = rbac_create_group("New Group for Something")

Deleting A Group
----------------

To delete a group through the API:

.. code-block:: python

  from rbac.views import rbac_delete_group

  rbac_delete_group(id)

This will also delete all users from the group by removing the entries from
RBACUserGroup (Django does this for us as a CASCADE).

Adding a Member to a Group
--------------------------

To add a member to a group through the API:

.. code-block:: python

  from rbac.views import rbac_add_user_to_group

  rbac_add_user_to_group(member, group)

Removing a Member from a Group
------------------------------

To remove a member from a group through the API:

.. code-block:: python

  from rbac.views import rbac_remove_user_from_group

  rbac_remove_user_from_group(member, group)

Adding a Role to a Group
------------------------

To add a role to a group through the API:

.. code-block:: python

  from rbac.views import rbac_add_role_to_group

  rbac_add_role_to_group(group, role)

Removing a Role from a Group
----------------------------

To add a role to a group through the API:

.. code-block:: python

  from rbac.views import rbac_remove_role_from_group

  rbac_remove_role_from_group(group, role)
