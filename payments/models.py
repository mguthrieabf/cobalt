from django.db import models
from django.conf import settings
from django.utils import timezone

class Balance(models.Model):
    system_number = models.IntegerField("%s Number" % settings.GLOBAL_ORG, blank=True, null=True)
    balance = models.DecimalField("Current Balance", blank=True, null=True, max_digits=10, decimal_places=2)
    last_top_up_date = models.DateTimeField("Last Top Up Date", auto_now_add=True, blank=True)
    last_top_up_amount = models.DecimalField("Last Top Up Amount", blank=True, null=True, max_digits=10, decimal_places=2)

    def __str__(self):
        return "%s" % self.system_number

class Transaction(models.Model):

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

    member = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    description = models.CharField("Description", max_length=100)
    amount = models.DecimalField("Amount", max_digits=8, decimal_places=2)
    status = models.CharField("Status", max_length=9, choices=TRANSACTION_STATUS, default='Initiated')
    stripe_reference = models.CharField("Stripe Payment Intent", null=True, max_length=40)
    stripe_method = models.CharField("Stripe Payment Method", null=True, max_length=40)
    stripe_currency = models.CharField("Card Native Currency", null=True, max_length=3)
    stripe_receipt_url = models.CharField("Receipt URL", null=True, max_length=200)
    stripe_brand = models.CharField("Card brand", null=True, max_length=10)
    stripe_country = models.CharField("Card Country", null=True, max_length=5)
    stripe_exp_month = models.IntegerField("Card Expiry Month", null=True)
    stripe_exp_year = models.IntegerField("Card Expiry Year", null=True)
    stripe_last4 = models.CharField("Card Last 4 Digits", null=True, max_length=4)
    route_code = models.CharField("Internal routing code for callback", null=True, max_length=4)
    route_payload = models.CharField("Payload to return to callback", null=True, max_length=40)
    created_date = models.DateTimeField("Creation Date", default=timezone.now)
    last_change_date = models.DateTimeField("Last Update Date", default=timezone.now)


    def __str__(self):
        return "%s(%s %s) - %s" % (self.member.abf_number, self.member.first_name,
                                  self.member.last_name, self.stripe_reference)

class Account(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    transaction = models.ForeignKey(Transaction, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField("Create Date", default=timezone.now)
    amount = models.DecimalField("Amount", max_digits=12, decimal_places=2)
    balance = models.DecimalField("Balance after transaction", max_digits=12, decimal_places=2)
    description = models.CharField("Transaction description", null=True, max_length=80)
    counterparty = models.CharField("Counterparty", null=True, max_length=80)

    def __str__(self):
        return "%s - %s %s %s" % (self.member.abf_number, self.member.first_name,
                                  self.member.last_name, self.id)
