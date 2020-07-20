from django import forms
from django.core.validators import RegexValidator
from .models import RBACAdminTree, RBACAdminUserGroup, RBACGroup, RBACAdminGroup


class AddGroup(forms.Form):
    """ Add a new group to RBAC """

    name_item = forms.CharField(
        label="Name",
        max_length=50,
        validators=[
            RegexValidator(
                regex=" ",
                message="Spaces are not allowed in the name",
                code="invalid_name_item",
                inverse_match=True,
            ),
        ],
    )
    description = forms.CharField(label="Description", max_length=50)
    add_self = forms.BooleanField(label="Add Yourself", required=False)

    # We need the logged in user to get the RBACTreeUser values, add a parameter to init
    # This is so we can build the drop down list dynamically
    def __init__(self, *args, **kwargs):
        # get user
        self.user = kwargs.pop("user", None)
        # get admin or normal
        self.environment = kwargs.pop("environment", None)
        # create form
        super(AddGroup, self).__init__(*args, **kwargs)
        choices = []
        group_list = RBACAdminUserGroup.objects.filter(member=self.user).values_list(
            "group"
        )
        queryset = RBACAdminTree.objects.filter(group__in=group_list)
        if self.environment == "admin":
            queryset = queryset.filter(tree__startswith="admin.")
        else:
            queryset = queryset.exclude(tree__startswith="admin.")
        for item in queryset:
            choices.append((item, item))
        self.fields["name_qualifier"] = forms.ChoiceField(
            label="Qualifier", choices=choices, required=False
        )

    def clean(self):
        """ We allow uses to put . into the name_item so here we split that
            out and put the part before the . into name_qualifier """
        super().clean()

        if not self.is_valid():
            return self.cleaned_data

        string = "%s.%s" % (
            self.cleaned_data["name_qualifier"],
            self.cleaned_data["name_item"],
        )
        parts = string.split(".")
        self.cleaned_data["name_qualifier"] = ".".join(parts[:-1])
        self.cleaned_data["name_item"] = parts[-1]

        # check for dupicates - this form is used by two models so load the right one
        if self.environment == "admin":
            dupe = RBACAdminGroup.objects.filter(
                name_qualifier=self.cleaned_data["name_qualifier"],
                name_item=self.cleaned_data["name_item"],
            ).exists()
        else:
            dupe = RBACGroup.objects.filter(
                name_qualifier=self.cleaned_data["name_qualifier"],
                name_item=self.cleaned_data["name_item"],
            ).exists()
        if dupe:
            msg = "%s.%s already taken" % (
                self.cleaned_data["name_qualifier"],
                self.cleaned_data["name_item"],
            )
            self._errors["name_qualifier"] = self.error_class([msg])
            self._errors["name_item"] = self.error_class([msg])

        return self.cleaned_data
