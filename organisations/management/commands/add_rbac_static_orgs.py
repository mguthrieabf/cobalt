from django.core.management.base import BaseCommand
from rbac.management.commands.rbac_core import (
    create_RBAC_admin_group,
    create_RBAC_admin_tree,
)
from rbac.core import rbac_add_user_to_admin_group, rbac_add_role_to_admin_group
from organisations.models import Organisation
from accounts.models import User

""" Create static within RBAC for Organisations

    Creates an admin group for every club with a corresponding place in the
    tree and rights to manage payments.

"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Running add_rbac_static_orgs")
        user = User.objects.filter(username="Mark").first()
        orgs = Organisation.objects.all()
        for org in orgs:
            item = org.name.replace(" ", "-")
            qualifier = f"org.abf.{org.state}"
            description = f"{org.name} Admins"

            if org.state != "" and org.state != " ":
                group = create_RBAC_admin_group(self, qualifier, item, description)
                create_RBAC_admin_tree(self, group, f"{qualifier}.{item}")
                rbac_add_user_to_admin_group(group, user)
                rbac_add_role_to_admin_group(
                    group, app="payments", model="manage", model_id=org.id
                )
