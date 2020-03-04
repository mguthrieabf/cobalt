from django.apps import AppConfig
import random
from django.db import connection
from django.db import connections

class NotificationsConfig(AppConfig):
    name = 'notifications'

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

        cursor = connection.cursor()
        cursor.execute('''SELECT version()''')
        row = cursor.fetchone()

        return(row)

#        return(random.choice(list))

    def acknowledge_notification(self, id):
        pass

    def add_notification(self, user, priority, msg):
        when="now"
        save="ok"
