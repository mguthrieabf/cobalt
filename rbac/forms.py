from django import forms
from .models import RBACUserTree


class AddGroup(forms.Form):
    """ Add a new group to RBAC """

    name_item = forms.CharField(label="Name", max_length=50)
    description = forms.CharField(label="Description", max_length=50)

    # We need the logged in user to get the RBACTreeUser values, add a parameter to init
    def __init__(self, *args, **kwargs):
        # get user
        self.user = kwargs.pop("user", None)
        # create form
        super(AddGroup, self).__init__(*args, **kwargs)
        # add field
        self.fields["name_qualifier"] = forms.ModelChoiceField(
            label="Qualifier", queryset=RBACUserTree.objects.filter(member=self.user)
        )
