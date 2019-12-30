from django.db import models
from django.conf import settings

class Balance(models.Model):
    system_number = models.IntegerField("%s Number" % settings.GLOBAL_ORG, blank=True, null=True)
    balance = models.DecimalField("Current Balance", blank=True, null=True, max_digits=10, decimal_places=2)
    last_top_up_date = models.DateTimeField("Last Top Up Date", auto_now_add=True, blank=True)
    last_top_up_amount = models.DecimalField("Last Top Up Amount", blank=True, null=True, max_digits=10, decimal_places=2)

    def __str__(self):
        return "%s" % self.system_number
