""" Notifications handles messages that Cobalt applications wish to pass to
    users.

    See `Notifications Overview`_ for more details.

.. _Notifications Overview:
   ./notifications_overview.html

"""

from django.shortcuts import render
import random
from django.db import connection
from django.db import connections
import boto3
from cobalt.settings import AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME, AWS_ACCESS_KEY_ID
from .models import InAppNotification

def get_notifications_for_user(user):
    notifications = {}
    notes = InAppNotification.objects.filter(member=user, acknowledged=False)
    for note in notes:
        notifications[note.id]=(note.message, note.link)
    return(notifications)

def get_stories_for_user(user):
    list=[
            "Welcome back.",
            "Good to see you.",
            "Hello.",
            "How are you?",
         ]
    # Create an SNS client
    # client = boto3.client(
    #     "sns",
    #     aws_access_key_id=AWS_ACCESS_KEY_ID,
    #     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    #     region_name=AWS_REGION_NAME
    # )
    #
    # # Send your sms message.
    # client.publish(
    #     PhoneNumber="+61423861767",
    #     Message="From Django",
    #     MessageAttributes={
    #         'AWS.SNS.SMS.SenderID': {
    #         'DataType': 'String',
    #         'StringValue': 'ABFTech'
    #         }
    #     }
    # )

#        return(row)

    return(random.choice(list))

def add_in_app_notification(member, msg, link=None):
    note = InAppNotification()
    note.member = member
    note.message = msg
    note.link = link
    note.save()

def acknowledge__in_app_notification(id):
    note = InAppNotification.objects.get(id=id)
    note.acknowledged = True
    note.save()

def delete__in_app_notification(id):
    InAppNotification.objects.filter(id=id).delete()
