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
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.CharField(max_length=100)
    comment = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    TRANSACTION_STATUS = [
        ('IN', 'Intent'),
        ('OK', 'Received'),
        ('CA', 'Cancelled'),
    ]

    status = models.CharField(
        max_length=2,
        choices=TRANSACTION_STATUS,
        default='IN',
    )
    created_date = models.DateTimeField(default=timezone.now)
    last_change_date = models.DateTimeField(default=timezone.now)
