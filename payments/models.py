from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string
from organisations.models import Organisation
from django.core.validators import MaxValueValidator

class StripeTransaction(models.Model):

    TRANSACTION_STATUS = [
    # This means we have asked a customer for money
        ('Initiated', 'Started - payment needs made'),
    # This means we have hit the checkout page and Stripe is waiting
        ('Intent', 'Intent - received customer intent to pay from Stripe'),
    # This means it worked and we have their cash
        ('Complete', 'Success - payment completed successfully'),
    # This means we didn't get their cash
        ('Failed', 'Failed - payment failed'),
    ]

    member = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL)
    description = models.CharField("Description", max_length=100)
    amount = models.DecimalField("Amount", max_digits=8, decimal_places=2)
    status = models.CharField("Status", max_length=9, choices=TRANSACTION_STATUS, default='Initiated')
    stripe_reference = models.CharField("Stripe Payment Intent", blank=True, null=True, max_length=40)
    stripe_method = models.CharField("Stripe Payment Method", blank=True, null=True, max_length=40)
    stripe_currency = models.CharField("Card Native Currency", blank=True, null=True, max_length=3)
    stripe_receipt_url = models.CharField("Receipt URL", blank=True, null=True, max_length=200)
    stripe_brand = models.CharField("Card brand", blank=True, null=True, max_length=10)
    stripe_country = models.CharField("Card Country", blank=True, null=True, max_length=5)
    stripe_exp_month = models.IntegerField("Card Expiry Month", blank=True, null=True)
    stripe_exp_year = models.IntegerField("Card Expiry Year", blank=True, null=True)
    stripe_last4 = models.CharField("Card Last 4 Digits", blank=True, null=True, max_length=4)
    route_code = models.CharField("Internal routing code for callback", blank=True, null=True, max_length=4)
    route_payload = models.CharField("Payload to return to callback", blank=True, null=True, max_length=40)
    created_date = models.DateTimeField("Creation Date", default=timezone.now)
    last_change_date = models.DateTimeField("Last Update Date", default=timezone.now)
    linked_organisation = models.ForeignKey(Organisation, blank=True, null=True, on_delete=models.SET_NULL)
    linked_transaction_type = models.CharField("Linked Transaction Type", blank=True, null=True, max_length=20)
    # linked amount can be different to amount if the member had some money in their account already
    linked_amount = models.DecimalField("Linked Amount", blank=True, null=True, max_digits=12, decimal_places=2)

    def __str__(self):
        return "%s(%s %s) - %s" % (self.member.system_number, self.member.first_name,
                                  self.member.last_name, self.stripe_reference)


class AbstractTransaction(models.Model):
    TRANSACTION_TYPE = [
        ('Transfer Out', 'Money transfered out of account'),
        ('Transfer In', 'Money transfered in to account'),
        ('Auto Top Up', 'Automated CC top up'),
        ('Congress Entry', 'Entry to a congress'),
        ('CC Payment', 'Credit Card payment'),
        ('Club Payment', 'Club game payment'),
        ('Club Membership', 'Club membership payment'),
        ('Miscellaneous', 'Miscellaneous payment'),
    ]

    created_date = models.DateTimeField("Create Date", default=timezone.now)
    amount = models.DecimalField("Amount", max_digits=12, decimal_places=2)
    balance = models.DecimalField("Balance After Transaction", max_digits=12, decimal_places=2)
    description = models.CharField("Transaction Description", blank=True, null=True, max_length=80)
    reference_no = models.CharField("Reference No", max_length=14, blank=True, null=True)
    type = models.CharField("Transaction Type", choices = TRANSACTION_TYPE, max_length=20)

    class Meta:
        abstract = True

class MemberTransaction(AbstractTransaction):
# This is the primary member whose account is being interacted with
    member = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="primary_member")

# Each record with have one of the following 3 things
# This is linked to a stripe transaction, so from our point of view this is money in
    stripe_transaction = models.ForeignKey(StripeTransaction, blank=True, null=True, on_delete=models.SET_NULL)
# It is linked to another member, so internal transfer to or from this member
# This will not have a stripe_transaction or an organisation set
    other_member = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, related_name="other_member")
# It is linked to an organisation so usually a payment to a club or congress for entry fees or subscriptions.
# Could also be a payment from the organisation for a refund for example.
# Can have a stripe_transaction as well
    organisation = models.ForeignKey(Organisation, blank=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = "%s-%s-%s" % (
                            ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
                            ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
                            ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)))
        super(MemberTransaction, self).save(*args, **kwargs)

    def __str__(self):
        return "%s - %s %s %s" % (self.member.system_number, self.member.first_name,
                                  self.member.last_name, self.id)

class OrganisationTransaction(AbstractTransaction):
    organisation = models.ForeignKey(Organisation, blank=True, null=True, on_delete=models.SET_NULL, related_name="primary_org")
# Organisation can have one and only one of the 3 following things
    member = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL)
    stripe_transaction = models.ForeignKey(StripeTransaction, blank=True, null=True, on_delete=models.SET_NULL)
    other_organisation = models.ForeignKey(Organisation, blank=True, null=True, on_delete=models.SET_NULL, related_name="secondary_org")

    def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = "%s-%s-%s" % (
                            ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
                            ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
                            ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)))
        super(OrganisationTransaction, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.organisation.name} - {self.id}"

    def __str__(self):
        return "%s (Stripe Customer id: %s)" % (self.member, self.stripe_customer_id)
