from django import forms
from .models import Congress, Event, Session
from organisations.models import Organisation
from .models import CongressMaster
from django_summernote.widgets import SummernoteInplaceWidget


class CongressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):

        # Get allowed congress masters as parameter
        congress_masters = kwargs.pop("congress_masters", [])
        super(CongressForm, self).__init__(*args, **kwargs)

        # Modify and congress master if  passed
        self.fields["congress_master"].queryset = CongressMaster.objects.filter(
            pk__in=congress_masters
        ).order_by("name")

        # Hide the crispy labels
        self.fields["name"].label = False
        self.fields["year"].label = False
        self.fields["start_date"].label = False
        self.fields["end_date"].label = False
        self.fields["date_string"].label = False
        self.fields["people"].label = False
        self.fields["people_array"].label = False
        self.fields["general_info"].label = False
        self.fields["venue_name"].label = False
        self.fields["venue_location"].label = False
        self.fields["venue_transport"].label = False
        self.fields["venue_catering"].label = False
        self.fields["venue_additional_info"].label = False
        self.fields["additional_info"].label = False
        self.fields["default_email"].label = False
        self.fields["sponsors"].label = False
        self.fields["payment_method_system_dollars"].label = False
        self.fields["payment_method_bank_transfer"].label = False
        self.fields["payment_method_cash"].label = False
        self.fields["payment_method_cheques"].label = False
        self.fields["entry_open_date"].label = False
        self.fields["entry_close_date"].label = False
        self.fields["allow_partnership_desk"].label = False

        # mark fields as optional
        self.fields["name"].required = False
        self.fields["year"].required = False
        self.fields["start_date"].required = False
        self.fields["end_date"].required = False
        self.fields["date_string"].required = False
        self.fields["people"].required = False
        self.fields["sponsors"].required = False
        self.fields["people_array"].required = False
        self.fields["general_info"].required = False
        self.fields["venue_name"].required = False
        self.fields["venue_location"].required = False
        self.fields["venue_transport"].required = False
        self.fields["venue_catering"].required = False
        self.fields["venue_additional_info"].required = False
        self.fields["additional_info"].required = False
        self.fields["default_email"].required = False
        self.fields["payment_method_system_dollars"].required = False
        self.fields["payment_method_bank_transfer"].required = False
        self.fields["payment_method_cash"].required = False
        self.fields["payment_method_cheques"].required = False
        self.fields["entry_open_date"].required = False
        self.fields["entry_close_date"].required = False
        self.fields["allow_partnership_desk"].required = False

    general_info = forms.CharField(
        widget=SummernoteInplaceWidget(
            attrs={
                "summernote": {
                    "height": "250",
                    "placeholder": "<br><br>Enter basic information about the congress.",
                }
            }
        )
    )

    sponsors = forms.CharField(
        widget=SummernoteInplaceWidget(
            attrs={
                "summernote": {
                    "height": "250",
                    "placeholder": "<br><br>(Optional) Enter information about sponsors and upload pictures and logos.",
                }
            }
        )
    )

    people = forms.CharField(
        widget=SummernoteInplaceWidget(attrs={"summernote": {"height": "250"}})
    )
    venue_transport = forms.CharField(
        widget=SummernoteInplaceWidget(
            attrs={
                "summernote": {
                    "height": "250",
                    "placeholder": "<br><br>Enter information about how to get to the venue, such as public transport or parking.",
                }
            }
        )
    )
    venue_catering = forms.CharField(
        widget=SummernoteInplaceWidget(
            attrs={
                "summernote": {
                    "height": "250",
                    "placeholder": "<br><br>Enter any information about catering that could be useful for attendees.",
                }
            }
        )
    )
    venue_additional_info = forms.CharField(
        widget=SummernoteInplaceWidget(
            attrs={
                "summernote": {
                    "height": "250",
                    "placeholder": "<br><br>Add any additional notes here.",
                }
            }
        )
    )
    additional_info = forms.CharField(
        widget=SummernoteInplaceWidget(
            attrs={
                "summernote": {
                    "height": "250",
                    "placeholder": "<br><br>Add any additional notes here. This appears at the bottom of the page and is not inside a box.",
                }
            }
        )
    )

    class Meta:
        model = Congress
        fields = (
            "congress_master",
            "year",
            "name",
            "start_date",
            "end_date",
            "date_string",
            "venue_name",
            "venue_location",
            "venue_transport",
            "venue_catering",
            "venue_additional_info",
            "additional_info",
            "people",
            "people_array",
            "raw_html",
            "general_info",
            "sponsors",
            "payment_method_system_dollars",
            "payment_method_bank_transfer",
            "payment_method_cash",
            "payment_method_cheques",
            "entry_open_date",
            "entry_close_date",
            "allow_partnership_desk",
            "default_email",
        )


class NewCongressForm(forms.Form):
    def __init__(self, *args, **kwargs):

        # Get valid orgs as parameter
        valid_orgs = kwargs.pop("valid_orgs", [])
        super(NewCongressForm, self).__init__(*args, **kwargs)

        org_queryset = Organisation.objects.filter(pk__in=valid_orgs).order_by("name")
        choices = [("", "-----------")]
        for item in org_queryset:
            choices.append((item.pk, item.name))
        self.fields["org"].choices = choices

    org = forms.ChoiceField(label="Organisation", required=False)
    congress_master = forms.IntegerField(label="Organisation", required=False)
    congress = forms.IntegerField(label="Organisation", required=False)


class EventForm(forms.ModelForm):

    entry_open_date = forms.DateField()

    class Meta:
        model = Event
        fields = (
            "event_name",
            "description",
            "max_entries",
            "event_type",
            "entry_open_date",
            "entry_close_date",
            "player_format",
        )


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = (
            "session_date",
            "session_start",
            "session_end",
        )
