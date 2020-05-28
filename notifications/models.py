from django.db import models
from django.utils import timezone
from django.conf import settings

class InAppNotification(models.Model):
    """ Temporary storage for notification messages.

    Stores any event that a Cobalt module wants to notify a user about.
    """

    member = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    message = models.CharField("Message",
        max_length=100
    )

    link = models.CharField("Link",
        max_length=50,
        blank=True,
        null=True
    )

    acknowledged = models.BooleanField(default=False)

    created_date = models.DateTimeField("Creation Date", default=timezone.now)

class NotificationMapping(models.Model):
    """ Stores mappings of users to events and actions  """

    NOTIFICATION_TYPES = [("SMS", "SMS Message"),
                          ("Email", "Email Message")
                         ]

    APPLICATION_NAMES = [("Forums", "Forums"),
                         ("Payments", "Payments")]

    member = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    application = models.CharField("Application",
        max_length=20,
        choices=APPLICATION_NAMES
    )
    """ Cobalt application name """

    event_type = models.CharField("Event Type",
        max_length=50)
    """ Event type as set by the application. eg. forum.post.new """

    topic = models.CharField("Topic",
        max_length=20
    )
    """ Level 1 event in application """

    subtopic = models.CharField("Sub-Topic",
        max_length=20,
        blank=True,
        null=True
    )
    """ Level 2 event in application """

    notification_type = models.CharField("Notification Type",
        max_length=5,
        choices=NOTIFICATION_TYPES,
        default='Email')
    """ How to notify the member """
