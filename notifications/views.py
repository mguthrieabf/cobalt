from django.shortcuts import render
import random
from django.db import connection
from django.db import connections
import boto3
from cobalt.settings import AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME, AWS_ACCESS_KEY_ID

class Notifications():

    def get_notifications_for_user(self, user):
        # print(user)
        # print(dir(user))
        # print(user.id)
        notifications = {
                         3456: ('You were 3rd at SABA', '/results/view=3456'),
                         4567: ('Notification from NSWBA', '/forums/view=4567')
                         }

        return(notifications)

    def get_stories_for_user(self, user):
        list=[
                "Welcome back.",
                "Good to see you.",
                "Hello.",
                "How are you?",
             ]

        # cursor = connection.cursor()
        # cursor.execute('''SELECT version()''')
        # row = cursor.fetchone()

        # Create an SNS client
        client = boto3.client(
            "sns",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION_NAME
        )

        # Send your sms message.
        client.publish(
            PhoneNumber="+61423861767",
            Message="From Django",
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {
                'DataType': 'String',
                'StringValue': 'ABFTech'
                }
            }
        )

#        return(row)

        return(random.choice(list))

    def acknowledge_notification(self, id):
        pass

    def add_notification(self, user, priority, msg):
        when="now"
        save="ok"
