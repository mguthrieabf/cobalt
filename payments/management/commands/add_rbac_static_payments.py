from django.core.management.base import BaseCommand
from rbac.management.commands.rbac_core import (
    create_RBAC_action,
    create_RBAC_default,
    create_RBAC_admin_group,
    create_RBAC_admin_tree,
)
from rbac.core import rbac_add_user_to_admin_group, rbac_add_role_to_admin_group
from accounts.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Running add_rbac_static_payments")
        create_RBAC_default(self, "payments", "manage", "Block")
        create_RBAC_action(self, "payments", "manage", "view")
        create_RBAC_action(self, "payments", "manage", "edit")
        create_RBAC_default(self, "payments", "global", "Block")
        create_RBAC_action(self, "payments", "global", "view")
        create_RBAC_action(self, "payments", "global", "edit")

        # Create admin groups for payments global
        user = User.objects.filter(username="Mark").first()
        group = create_RBAC_admin_group(
            self,
            "org.abf.abf",
            "global-finance",
            "Group for administration of central finance functions",
        )
        create_RBAC_admin_tree(self, group, "org.abf.abf.global-finance")
        rbac_add_user_to_admin_group(group, user)
        rbac_add_role_to_admin_group(group, app="payments", model="global")
