from django import forms
from .models import RBACAdminTree, RBACAdminUserGroup


class AddGroup(forms.Form):
    """ Add a new group to RBAC """

    name_item = forms.CharField(label="Name", max_length=50)
    description = forms.CharField(label="Description", max_length=50)
    add_self = forms.BooleanField(label="Add Yourself", required=False)

    # We need the logged in user to get the RBACTreeUser values, add a parameter to init
    # This is so we can build the drop down list dynamically
    def __init__(self, *args, **kwargs):
        # get user
        self.user = kwargs.pop("user", None)
        # create form
        super(AddGroup, self).__init__(*args, **kwargs)
        # add field - always include users home location as an option
        # choices = [
        #     (
        #         f"rbac.users.{self.user.system_number}",
        #         f"rbac.users.{self.user.system_number}",
        #     )
        # ]
        choices = []
        group_list = RBACAdminUserGroup.objects.filter(member=self.user).values_list(
            "group"
        )
        queryset = RBACAdminTree.objects.filter(group__in=group_list)
        for item in queryset:
            choices.append((item, item))
        self.fields["name_qualifier"] = forms.ChoiceField(
            label="Qualifier", choices=choices, required=False
        )
