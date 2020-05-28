""" values set in here are passed to every template """

from django.conf import settings
from notifications.views import get_notifications_for_user

def global_settings(request):

    if request.user.is_anonymous:
        notifications={}
    else:
        print("#################")
        print(request.user)
        notifications = get_notifications_for_user(request.user)
        print("#################")

    print(notifications)

    return {
            'notifications': notifications,
            'GLOBAL_ORG': settings.GLOBAL_ORG,
            'GLOBAL_TITLE': settings.GLOBAL_TITLE,
            'GLOBAL_CONTACT': settings.GLOBAL_CONTACT,
            'GLOBAL_ABOUT': settings.GLOBAL_ABOUT,
            'GLOBAL_PRIVACY': settings.GLOBAL_PRIVACY,
            'GLOBAL_MPSERVER': settings.GLOBAL_MPSERVER,
            'GLOBAL_PRODUCTION': settings.GLOBAL_PRODUCTION,
            'GLOBAL_CURRENCY_SYMBOL': settings.GLOBAL_CURRENCY_SYMBOL,
            'GLOBAL_CURRENCY_NAME': settings.GLOBAL_CURRENCY_NAME,
            'AUTO_TOP_UP_MAX_AMT': settings.AUTO_TOP_UP_MAX_AMT,
            'AUTO_TOP_UP_MIN_AMT': settings.AUTO_TOP_UP_MIN_AMT,
            'AUTO_TOP_UP_LOW_LIMIT': settings.AUTO_TOP_UP_LOW_LIMIT,
           }
