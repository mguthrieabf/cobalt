from django import forms
from .models import Congress
from organisations.models import Organisation
from django_summernote.widgets import SummernoteInplaceWidget


class CongressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):

        # Get valid orgs as parameter
        valid_orgs = kwargs.pop("valid_orgs", None)
        super(CongressForm, self).__init__(*args, **kwargs)
        # Modify valid orgs if they were passed
        self.fields["org"].queryset = Organisation.objects.filter(pk__in=valid_orgs)

        # Hide the crispy labels
        self.fields["name"].label = False
        self.fields["year"].label = False
        self.fields["date_string"].label = False
        self.fields["org"].label = False
        self.fields["venue_name"].label = False
        self.fields["venue_location"].label = False
        self.fields["venue_transport"].label = False
        self.fields["venue_catering"].label = False
        self.fields["venue_additional_info"].label = False

    # name = forms.CharField(
    #     widget=forms.TextInput(attrs={"class": "cobalt-min-width-100"})
    # )

    venue_transport = forms.CharField(
        widget=SummernoteInplaceWidget(
            # attrs={
            #     "summernote": {
            #         "placeholder": "<br><br>Write your article. <br><br>You can enter card symbols and hand diagrams from the toolbar."
            #     }
            # }
        )
    )
    venue_catering = forms.CharField(
        widget=SummernoteInplaceWidget(
            # attrs={
            #     "summernote": {
            #         "placeholder": "<br><br>Write your article. <br><br>You can enter card symbols and hand diagrams from the toolbar."
            #     }
            # }
        )
    )
    venue_additional_info = forms.CharField(
        widget=SummernoteInplaceWidget(
            # attrs={
            #     "summernote": {
            #         "placeholder": "<br><br>Write your article. <br><br>You can enter card symbols and hand diagrams from the toolbar."
            #     }
            # }
        )
    )

    class Meta:
        model = Congress
        fields = (
            "congress_master",
            "year",
            "name",
            "date_string",
            "org",
            "venue_name",
            "venue_location",
            "venue_transport",
            "venue_catering",
            "venue_additional_info",
        )
