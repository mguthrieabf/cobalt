from django.core.management.base import BaseCommand
from rbac.management.commands.rbac_core import create_RBAC_action, create_RBAC_default


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Running add_rbac_static_forums")
        create_RBAC_default(self, "forums", "forum", "Allow")
        create_RBAC_action(self, "forums", "forum", "create")
        create_RBAC_action(self, "forums", "forum", "delete")
        create_RBAC_action(self, "forums", "forum", "view")
        create_RBAC_action(self, "forums", "forum", "edit")
        create_RBAC_action(self, "forums", "forum", "moderate")

        create_RBAC_default(self, "forums", "forumadmin", "Block")
        create_RBAC_action(self, "forums", "forum", "change")
