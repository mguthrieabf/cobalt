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
* payments.manage - Block

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
---------

The following roles are important:

* forums.forumadmin [Allow] - allows the management of forums, e.g. create, modify and
  delete.

* forums.forum.view [Allow] - can view posts in any forum

* forums.forum.create [Allow] - can create posts or respond to posts in any forum

* forums.forum.moderate [Allow] - can moderate in any forum. Moderators can
  edit any post or comment (not delete them) and can block users from posting
  in a specific forum.

* forums.forum.N.view [Allow] - can view posts in forum N.

* forums.forum.N.create [Allow] - can create posts or respond to posts in forum N.

* forums.forum.moderate [Allow] - can moderate in forum N. Moderators can
  edit any post or comment (not delete them) and can block users from posting 
  in a specific forum.

*



  +------------------------+-----------------------------------------+
  | Role                   | Purpose                                 |
  +========================+=========================================+
  | forums.forum.x         | *Ability to do something in forum x*    |
  +------------------------+-----------------------------------------+
  | forums.forum           | *Ability to do something in all forums* |
  +------------------------+-----------------------------------------+
  | forums.forumadmin      | *Make changes at the forum level*       |
  +------------------------+-----------------------------------------+
  | payments.view.x        | *View payments for org x*               |
  +------------------------+-----------------------------------------+
  | payments.view          | *View payments for any org*             |
  +------------------------+-----------------------------------------+
  | payments.manage.x      | *Do things with payments for org x*     |
  +------------------------+-----------------------------------------+
  | payments.manage        | *Do things with payments for any org*   |
  +------------------------+-----------------------------------------+
  | org.org.x              | *Management of org x*                   |
  +------------------------+-----------------------------------------+
  | org.org                | *Management of all orgs*                |
  +------------------------+-----------------------------------------+
