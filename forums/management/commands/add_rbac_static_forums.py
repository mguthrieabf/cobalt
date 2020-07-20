from django.core.management.base import BaseCommand
from rbac.management.commands.rbac_core import (
    create_RBAC_action,
    create_RBAC_default,
    create_RBAC_admin_group,
    create_RBAC_admin_tree,
)
from rbac.core import (
    rbac_add_user_to_admin_group,
    rbac_add_role_to_admin_group,
)
from accounts.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Running add_rbac_static_forums")

        # basic forums behaviours
        create_RBAC_default(self, "forums", "forum", "Allow")
        create_RBAC_action(self, "forums", "forum", "create")
        create_RBAC_action(self, "forums", "forum", "delete")
        create_RBAC_action(self, "forums", "forum", "view")
        create_RBAC_action(self, "forums", "forum", "edit")
        create_RBAC_action(self, "forums", "forum", "moderate")

        # Forum admin
        create_RBAC_default(self, "forums", "forumadmin", "Block")
        create_RBAC_action(self, "forums", "forumadmin", "change")

        # add myself as an admin and create tree and group
        # This lets us create admins who can create and delete forums
        user = User.objects.filter(username="Mark").first()

        group = create_RBAC_admin_group(
            self,
            "admin.abf.forums",
            "forumadmin",
            "Group to create users who can create, modify or delete forums",
        )
        create_RBAC_admin_tree(self, group, "rbac.abf.forums")
        rbac_add_user_to_admin_group(group, user)
        rbac_add_role_to_admin_group(group, app="forums", model="forumadmin")

        # grant writes to forums.forum
        # This creates admins who can make people moderators or block forum access
        group = create_RBAC_admin_group(
            self,
            "admin.abf.forums",
            "moderators",
            "Group to create users who are moderators of forums or can hide forums",
        )
        # create group - won't duplicate if already exists
        create_RBAC_admin_tree(self, group, "rbac.abf.forums")
        rbac_add_user_to_admin_group(group, user)
        rbac_add_role_to_admin_group(group, app="forums", model="forum")
