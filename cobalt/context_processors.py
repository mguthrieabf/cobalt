from django.conf import settings

def global_settings(request):
    # Global values to configure by installation
    return {
            'GLOBAL_ORG': settings.GLOBAL_ORG,
            'GLOBAL_TITLE': settings.GLOBAL_TITLE,
           }
