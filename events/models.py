from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from organisations.models import Organisation
from accounts.models import User
from payments.models import MemberTransaction

PAYMENT_STATUSES = [
    ("Paid", "Entry Paid"),
    ("Pending Manual", "Pending Manual Payment"),
    ("Unpaid", "Entry Unpaid"),
]
CONGRESS_STATUSES = [
    ("Draft", "Draft"),
    ("Published", "Published"),
    ("Closed", "Closed"),
]
EVENT_TYPES = [
    ("Open", "Open"),
    ("Restricted", "Restricted"),
    ("Novice", "Novice"),
    ("Senior", "Senior"),
    ("Youth", "Youth"),
]
EVENT_PLAYER_FORMAT = [
    ("Individual", "Individual"),
    ("Pairs", "Pairs"),
    ("Teams", "Teams"),
]


class CongressMaster(models.Model):
    """ Master List of congresses. E.g. GCC. This is not an instance
       of a congress, just a list of the regular recurring ones.
       Congresses can only belong to one club at a time. Control for
       who can setup a congress as an instance of a congress master
       is handled by who is a convener for a club """

    name = models.CharField("Congress Master Name", max_length=100)
    org = models.ForeignKey(Organisation, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Congress(models.Model):
    """ A specific congress including year

    We set all values to be optional so we can use the wizard format and
    save partial data as we go. The validation for completeness of data
    lies in the view. """

    name = models.CharField("Name", max_length=100, null=True, blank=True)
    default_email = models.CharField(
        "Default Email Address", max_length=100, null=True, blank=True
    )
    date_string = models.CharField("Dates", max_length=100, null=True, blank=True)
    congress_master = models.ForeignKey(
        CongressMaster, on_delete=models.CASCADE, null=True, blank=True
    )
    year = models.IntegerField("Congress Year", null=True, blank=True)
    org = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, null=True, blank=True
    )
    venue_name = models.CharField("Venue Name", max_length=100, null=True, blank=True)
    venue_location = models.CharField(
        "Venue Location", max_length=100, null=True, blank=True
    )
    venue_transport = models.TextField("Venue Transport", null=True, blank=True)
    venue_catering = models.TextField("Venue Catering", null=True, blank=True)
    venue_additional_info = models.TextField(
        "Venue Additional Information", null=True, blank=True
    )
    additional_info = models.TextField(
        "Congress Additional Information", null=True, blank=True
    )
    raw_html = models.TextField("Raw HTML", null=True, blank=True)
    people = models.TextField("People", null=True, blank=True)
    people_array = ArrayField(
        ArrayField(models.CharField(max_length=30, null=True, blank=True)),
        null=True,
        blank=True,
    )
    general_info = models.TextField("General Information", null=True, blank=True)
    payment_method_system_dollars = models.BooleanField(default=True)
    payment_method_bank_transfer = models.BooleanField(default=False)
    payment_method_cash = models.BooleanField(default=False)
    payment_method_cheques = models.BooleanField(default=False)
    # Open and close dates can be overriden at the event level
    entry_open_date = models.DateTimeField(null=True, blank=True)
    entry_close_date = models.DateTimeField(null=True, blank=True)
    allow_partnership_desk = models.BooleanField(default=False)
    author = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="author", null=True, blank=True
    )
    created_date = models.DateTimeField(default=timezone.now)
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="last_updated_by",
    )
    last_updated = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        "Congress Status", max_length=10, choices=CONGRESS_STATUSES, default="Draft"
    )

    def __str__(self):
        return "%s - %s" % (self.congress_master, self.year)


class Event(models.Model):
    """ An event within a congress """

    congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
    event_name = models.CharField("Event Name", max_length=100)
    description = models.CharField("Description", max_length=400, null=True, blank=True)
    max_entries = models.IntegerField("Maximum Entries", null=True, blank=True)
    event_type = models.CharField(
        "Event Type", max_length=14, choices=EVENT_TYPES, null=True, blank=True
    )
    # Open and close dates can be overriden at the event level
    entry_open_date = models.DateTimeField(null=True, blank=True)
    entry_close_date = models.DateTimeField(null=True, blank=True)
    player_format = models.CharField(
        "Player Format",
        max_length=14,
        choices=EVENT_PLAYER_FORMAT,
        null=True,
        blank=True,
    )

    def __str__(self):
        return "%s - %s" % (self.congress, self.event_name)


class Session(models.Model):
    """ A session within an event """

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    session_date = models.DateField()
    session_start = models.TimeField()
    session_end = models.TimeField(null=True, blank=True)


class EventEntryType(models.Model):
    """ A type of event entry - e.g. full, junior, senior """

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    event_entry_type = models.CharField("Event Entry Type", max_length=20)
    entry_fee = models.DecimalField("Full Entry Fee", decimal_places=2, max_digits=10)

    def __str__(self):
        return "%s - %s" % (self.event, self.event_emtry_type)


class EventEntry(models.Model):
    """ An entry to an event """

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    payment_status = models.CharField("Event Name", max_length=100)
    max_entries = models.IntegerField("Maximum Entries", null=True, blank=True)
    payment_status = models.CharField(
        "Payment Status", max_length=20, choices=PAYMENT_STATUSES, default="Unpaid"
    )

    def __str__(self):
        return "%s - %s" % (self.congress, self.event_name)


class EventEntryPlayer(models.Model):
    """ A player who is entering an event """

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    player_payment_record = models.ForeignKey(
        MemberTransaction, on_delete=models.CASCADE, null=True, blank=True
    )
    payment_status = models.CharField(
        "Payment Status", max_length=20, choices=PAYMENT_STATUSES, default="Unpaid"
    )

    def __str__(self):
        return "%s - %s" % (self.event, self.player)


class CongressLink(models.Model):
    """ Link Items for Congresses """

    congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
    link = models.CharField("Congress Link", max_length=100)

    def __str__(self):
        return "%s" % (self.congress)


class CongressNewsItem(models.Model):
    """ News Items for Congresses """

    congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return "%s" % (self.congress)


#
# class CongressPeople(models.Model):
#     """ Roles within a congress """
#
#     congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     user_role = models.CharField("User Role", max_length=50)
#     email = models.CharField("Email", max_length=50, null=True, blank=True)
#     phone = models.CharField("Phone Number", max_length=10, null=True, blank=True)
#
#     def __str__(self):
#         return "%s - %s" % (self.congress, self.user)


class CongressDownload(models.Model):
    """ Downloadable items for Congresses """

    congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
    text = models.TextField()  # fix later
