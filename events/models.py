from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from organisations.models import Organisation
from accounts.models import User
from payments.models import MemberTransaction
from cobalt.settings import GLOBAL_ORG, GLOBAL_CURRENCY_SYMBOL, TIME_ZONE
import datetime
import pytz

PAYMENT_STATUSES = [
    ("Paid", "Entry Paid"),
    ("Pending Manual", "Pending Manual Payment"),
    ("Unpaid", "Entry Unpaid"),
]
PAYMENT_TYPES = [
    ("System dollars", "%s %s" % (GLOBAL_ORG, GLOBAL_CURRENCY_SYMBOL)),
    ("Bank Transfer", "Bank Transfer"),
    ("Cash", "Cash"),
    ("Cheque", "Cheque"),
    ("Unknown", "Unknown"),
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
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    date_string = models.CharField("Dates", max_length=100, null=True, blank=True)
    congress_master = models.ForeignKey(
        CongressMaster, on_delete=models.CASCADE, null=True, blank=True
    )
    year = models.IntegerField("Congress Year", null=True, blank=True)
    # org = models.ForeignKey(
    #     Organisation, on_delete=models.CASCADE, null=True, blank=True
    # )
    venue_name = models.CharField("Venue Name", max_length=100, null=True, blank=True)
    venue_location = models.CharField(
        "Venue Location", max_length=100, null=True, blank=True
    )
    venue_transport = models.TextField("Venue Transport", null=True, blank=True)
    venue_catering = models.TextField("Venue Catering", null=True, blank=True)
    venue_additional_info = models.TextField(
        "Venue Additional Information", null=True, blank=True
    )
    sponsors = models.TextField("Sponsors", null=True, blank=True)
    additional_info = models.TextField(
        "Congress Additional Information", null=True, blank=True
    )
    raw_html = models.TextField("Raw HTML", null=True, blank=True)
    people = models.TextField("People", null=True, blank=True)

    general_info = models.TextField("General Information", null=True, blank=True)
    links = models.TextField("Links", null=True, blank=True)
    payment_method_system_dollars = models.BooleanField(default=True)
    payment_method_bank_transfer = models.BooleanField(default=False)
    bank_transfer_details = models.TextField(
        "Bank Transfer Details", null=True, blank=True
    )
    payment_method_cash = models.BooleanField(default=False)
    payment_method_cheques = models.BooleanField(default=False)
    cheque_details = models.TextField("Cheque Details", null=True, blank=True)
    allow_early_payment_discount = models.BooleanField(default=False)
    early_payment_discount_date = models.DateTimeField(
        "Last day for early discount", null=True, blank=True
    )
    allow_youth_payment_discount = models.BooleanField(default=False)
    youth_payment_discount_date = models.DateTimeField(
        "Date for age check", null=True, blank=True
    )
    youth_payment_discount_age = models.IntegerField("Cut off age", default=30)
    senior_date = models.DateTimeField("Date for age check", null=True, blank=True)
    senior_age = models.IntegerField("Cut off age", default=60)
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
    entry_fee = models.DecimalField("Entry Fee", max_digits=12, decimal_places=2)
    entry_early_payment_discount = models.DecimalField(
        "Early Payment Discount", max_digits=12, decimal_places=2, null=True, blank=True
    )
    entry_youth_payment_discount = models.DecimalField(
        "Youth Discount", max_digits=12, decimal_places=2, null=True, blank=True
    )

    player_format = models.CharField(
        "Player Format",
        max_length=14,
        choices=EVENT_PLAYER_FORMAT,
        null=True,
        blank=True,
    )

    def __str__(self):
        return "%s - %s" % (self.congress, self.event_name)

    def is_open(self):
        """ check if this event is taking entries today """

        today = timezone.now().date()
        open_date = self.event_open_date
        if not open_date:
            open_date = self.congress.entry_open_date
        if today < open_date:
            return False

        close_date = self.event_close_date
        if not close_date:
            close_date = self.congress.entry_close_date
        if today > close_date:
            return False

        return True

    def entry_fee_for(self, user):
        """ return entry fee for user based on age and date """

        # default
        entry_fee = self.entry_fee
        discount = 0.0
        reason = "Full fee"

        # date
        if self.congress.allow_early_payment_discount:
            today = timezone.now()
            if self.congress.early_payment_discount_date >= today:
                entry_fee = self.entry_fee - self.entry_early_payment_discount
                reason = "Early discount"
                discount = self.entry_early_payment_discount

        # youth
        if self.congress.allow_youth_payment_discount:
            if user.dob:  # skip if no date of birth set
                dob = datetime.datetime.combine(user.dob, datetime.time(0, 0))
                dob = timezone.make_aware(dob, pytz.timezone(TIME_ZONE))
                ref_date = dob.replace(
                    year=dob.year + self.congress.youth_payment_discount_age
                )
                if self.congress.youth_payment_discount_date <= ref_date:
                    youth_fee = self.entry_fee - self.entry_youth_payment_discount
                    if youth_fee < entry_fee:
                        entry_fee = youth_fee
                        reason = "Youth discount"
                        discount = self.entry_youth_payment_discount

        return entry_fee, discount, reason


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
    payment_status = models.CharField(
        "Payment Status", max_length=20, choices=PAYMENT_STATUSES, default="Unpaid"
    )
    payment_type = models.CharField(
        "Payment Type", max_length=20, choices=PAYMENT_TYPES, default="Unknown"
    )
    primary_entrant = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s - %s" % (
            self.event.congress,
            self.event.event_name,
            self.primary_entrant,
        )


class EventEntryPlayer(models.Model):
    """ A player who is entering an event """

    event_entry = models.ForeignKey(EventEntry, on_delete=models.CASCADE)
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


class CongressDownload(models.Model):
    """ Downloadable items for Congresses """

    congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
    text = models.TextField()  # fix later
