from django.core.management.base import BaseCommand
from rbac.management.commands.rbac_core import create_RBAC_action, create_RBAC_default


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Running add_rbac_static_payments")
        create_RBAC_default(self, "payments", "manage", "Block")
        create_RBAC_action(self, "payments", "manage", "view")
        create_RBAC_action(self, "payments", "manage", "edit")
