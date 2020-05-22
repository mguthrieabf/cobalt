from django.db import models
from django.utils import timezone
from django.conf import settings

class InAppNotification(models.Model):
    """ Temporary storage for notification messages.

    Stores any event that a Cobalt module wants to notify a user about.
    """

    member = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                               on_delete=models.SET_NULL)
    message = models.CharField("Message", max_length=100)
    link = models.CharField("Link", max_length=50, blank=True, null=True)
    acknowledged = models.BooleanField(default=False)
    created_date = models.DateTimeField("Creation Date", default=timezone.now)
