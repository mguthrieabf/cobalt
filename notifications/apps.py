from django.apps import AppConfig
import random


class NotificationsConfig(AppConfig):
    name = 'notifications'

class Notifications():

    def get_notifications_for_user(self, user):
        print(user)
        print(dir(user))
        print(user.id)
        notifications = {
                         3456: 'Notify 1 - test',
                         4567: 'Notify 2 - test'
                         }

        return(notifications)

    def get_stories_for_user(self, user):
        list=[
                "Welcome back.",
                "Good to see you.",
                "Hello.",
                "How are you?",
             ]
        return(random.choice(list))

    def acknowledge_notification(self, id):
        pass
