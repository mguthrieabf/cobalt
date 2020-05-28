""" Notifications handles messages that Cobalt applications wish to pass to users.

    See `Notifications Overview`_ for more details.

.. _Notifications Overview:
   ./notifications_overview.html

"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import random
from django.db import connection
from django.db import connections
import boto3
from cobalt.settings import AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME, AWS_ACCESS_KEY_ID
from .models import InAppNotification, NotificationMapping
from django.core.mail import send_mail
from django.utils.html import strip_tags
from cobalt.settings import DEFAULT_FROM_EMAIL, GLOBAL_TITLE

def send_cobalt_email(to_address, subject, msg):
    """ Send single email

    Args:
        to_address (str): who to send to
        subject (str): subject line for email
        msg (str): message to send in HTML or plain format

    Returns:
        Nothing
    """

    plain_msg = strip_tags(msg)
    send_mail(subject, plain_msg, DEFAULT_FROM_EMAIL, [to_address], html_message=msg)

def send_cobalt_sms(phone_number, msg):
    """ Send single SMS

    Args:
        phone_number (str): who to send to
        msg (str): message to send

    Returns:
        Nothing
    """

    client = boto3.client(
        "sns",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION_NAME
    )

    client.publish(
        PhoneNumber=phone_number,
        Message=msg,
        MessageAttributes={
            'AWS.SNS.SMS.SenderID': {
            'DataType': 'String',
            'StringValue': GLOBAL_TITLE
            }
        }
    )

def get_notifications_for_user(user):
    """ Get a list of all unacklowledged notifications for a user

    Returns a list of notifications for the user where the status is
    unacknowledged.

    TODO: Limit the size of the list. Maybe add a home page to manage them.

    Args:
        user (User): standard User object

    Returns:
        list: List of notifications which themselves are dictionaries
    """

    notifications = {}
    notes = InAppNotification.objects.filter(member=user, acknowledged=False)
    for note in notes:
        notifications[note.id]=(note.message, note.link)
    return(notifications)

def contact_member(member, msg, contact_type, link=None, html_msg=None,
                   subject=None):
    """ Contact member using their preferred method """

    if not subject:
        subject = "Notification from ABFTech"

    # Always create an in app notification
    add_in_app_notification(member, msg, link)

    if contact_type == "Email":
        send_cobalt_email(member.email, subject, msg)
    if contact_type == "SMS":
        send_cobalt_sms(member.mobile, msg)

def create_user_notification(member, application_name, event_type, topic,
                             subtopic=None, notification_type="Email"):
    """ create a notification record for a user

    Used to programatically create a notification record. For example Forums
    will call this to register a notification for comments on a users post.

    Args:
        member - standard User object
        application_name - name of the Cobalt application to follow
        event_type - event e.g. forums.post.comment
        topic - specific to the application
        notification type - email or SMS

    Returns:
        Nothing
    """

    notification = NotificationMapping()
    notification.member = member
    notification.application = application_name
    notification.event_type = event_type
    notification.topic = topic
    notification.subtopic = subtopic
    notification.notification_type = notification_type
    notification.save()

def notify_happening_forums(application_name, event_type, msg, topic, subtopic=None,
                            link=None, html_msg=None):
    """ sub function for notify_happening() - handles Forum events
        Might be able to make this generic
    """

    print("Incoming event:")
    print("Event tpye: %s" % event_type)
    print("App: %s" % application_name)
    print("Topic: %s" % topic)
    print("Subtopic: %s" % subtopic)

    listeners=[]

    if topic and subtopic:
        listeners = NotificationMapping.objects.filter(application=application_name,
                        event_type=event_type, topic=topic, subtopic=subtopic)
    elif topic:
        listeners = NotificationMapping.objects.filter(application=application_name,
                        event_type=event_type, topic=topic, subtopic=None)

    print(listeners)
    l = NotificationMapping.objects.all()
    for x in l:
        print(x.event_type)
        print(event_type)
        print(x.application)
        print(application_name)
        print(x.member)
        print(x.topic)
        print(topic)
        print(x.subtopic)
        print(subtopic)


    for listener in listeners:
        print(listener)
        contact_member(listener.member, msg, listener.notification_type, link, html_msg)


def notify_happening(application_name, event_type, msg, topic, subtopic=None, link=None,
                     html_msg=None):
    """ Called by Cobalt applications to tell notify they have done something.

    Main entry point for general notifications of events within the system.
    Applications publish an event through this call and Notifications tells
    any member who has registered an interest in this event.

    Args:
        application_name - name of the calling app
        topic - specific to the application, high level event
        subtopic - specific to the application, next level event
        msg - a brief description of the event
        link - an HTML relative link to the event (Optional)
        html_msg - a long description of the event

    Returns:
        Nothing

    """
    print("inside notify happening")
    if application_name == "Forums":
        notify_happening_forums(application_name, event_type, msg, topic, subtopic, link,
                                html_msg)

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
