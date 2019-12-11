from django.conf import settings

def global_settings(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
            'GLOBAL_ORG': settings.GLOBAL_ORG,
            'GLOBAL_TITLE': settings.GLOBAL_TITLE,
           }
