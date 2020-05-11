from django.conf import settings

def global_settings(request):
    # Global values to configure by installation
    return {
            'GLOBAL_ORG': settings.GLOBAL_ORG,
            'GLOBAL_TITLE': settings.GLOBAL_TITLE,
            'GLOBAL_CONTACT': settings.GLOBAL_CONTACT,
            'GLOBAL_ABOUT': settings.GLOBAL_ABOUT,
            'GLOBAL_PRIVACY': settings.GLOBAL_PRIVACY,
            'GLOBAL_MPSERVER': settings.GLOBAL_MPSERVER,
            'GLOBAL_PRODUCTION': settings.GLOBAL_PRODUCTION,
           }
