.. _rbac_ABF_Roles:


.. image:: images/cobalt.jpg
 :width: 300
 :alt: Cobalt Chemical Symbol

RBAC ABF Roles
==============

This page lists the roles and groups that are set up for the ABF version
of Cobalt. See `rbac_overview` for details on the module itself.

The tree structure (both the RBAC tree and the Admin tree) are only to
provide an organised way to manage a potential large number of groups.
They do not affect the security in any way. The only thing that really matters
in terms of controlling access is the roles that are added to a group and the
user who are members of that group.

This page lists the roles required for different functions and then also
the groups (and their location in the tree) that have been set up to accomodate
this.

RBAC Defaults
-------------

Defaults apply when no matching rule can be found.

* forums.forum - Allow
* forums.forumadmin - Block
* payments.global - Block
* payments.org - Block
* org.org - Block

Hierarchy
---------

Roles can be one of two main formats:

* app.model.action e.g. forums.forum.view
* app.model.model_id.action e.g. forums.forums.6.view

The higher level role (without the number) will also apply to the lower level
when checking. So for example if a user needs forums.forum.5.create for an
action, then if they have forums.forum.create that will be used. However,
specific rules have precedence. e.g. if a user has forums.forums.create Block,
and forums.forums.5.create Allow, then they will be allowed to post in forum 5.

The forum numbers (and other model_ids) are the internal representation of the
model (primary key). If necessary they can be mapped to a name, but for RBAC
it is more efficient to use the number.

RBAC All
--------

A role of "All" matches on any action. e.g. if a group has forums.forum.all
it will match against forums.forum.create or forums.forum.5.view (specifically for
forums, moderate is done a little differently and is excluded from all).

RBAC EVERYONE
-------------

The EVERYONE user matches against any user, so adding EVERYONE to a group is
the same as individually adding all users to the group.

Key Roles
=========

Forums
------

The following roles are important:

* **forums.forumadmin** [*Allow*] - allows the management of forums, e.g. create, modify and
  delete.

* **forums.forum.view** [*Allow*] - can view posts in any forum

* **forums.forum.create** [*Allow*] - can create posts or respond to posts in any forum

* **forums.forum.moderate** [*Allow*] - can moderate in any forum. Moderators can
  edit any post or comment (not delete them) and can block users from posting
  in a specific forum.

* **forums.forum.N.view** [*Allow*] - can view posts in forum N.

* **forums.forum.N.create** [*Allow*] - can create posts or respond to posts in forum N.

* **forums.forum.moderate** [*Allow*] - can moderate in forum N. Moderators can
  edit any post or comment (not delete them) and can block users from posting
  in a specific forum.

Payments
--------

* **payments.org.view** [*Allow*] - can view statements for all organisations.

* **payments.org.N.view** [*Allow*] - can view statements for organisation N.

* **payments.org.manage** [*Allow*] - can manage payments for all organisations.

* **payments.org.N.manage** [*Allow*] - can manage payments for organisation N.

Organisations
-------------

* **org.org.view** [*Allow*] - can view details about all organisations.

* **org.org.N.view** [*Allow*] - can view details about organisation N.

* **org.org.edit** [*Allow*] - can edit details about all organisations.

* **org.org.N.edit** [*Allow*] - can edit details about organisation N.

Groups and Trees
================

As mentioned above, the groups and trees (normal and admin) are just a way to index
things, the names are arbitrary.

For convenience (or inconvenience!) the admin tree mirrors the normal tree.

Normal Tree: rbac.forums.forum.5

Admin Tree: admin.forums.forum.5

Groups can (and should) contain multiple roles. This means that they cannot
easily match the "tree" structure of roles. The RBAC tree reflects functions
that users need to perform, such as "System Administrator", "Club N Directors",
"State N Financial Controllers".

Groups
------

This is the basic structure of the tree and groups for RBAC.

  +------------------------+-----------------------------------------+
  | Group / Tree           | Purpose                                 |
  +========================+=========================================+
  | rbac.clubs.N           | *Things relating to club N*             |
  |                        | e.g. rbac.clubs.N.directors             |
  |                        | rbac.clubs.N.finance                    |
  +------------------------+-----------------------------------------+
  | rbac.abf               | *Things relating to the ABF*            |
  |                        | e.g. rbac.abf.finance                   |
  |                        | rbac.abf.forumadmins                    |
  +------------------------+-----------------------------------------+
