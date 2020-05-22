from django.contrib import admin
from .models import InAppNotification

class InAppNotificationAdmin(admin.ModelAdmin):
    search_fields = ('member',)

admin.site.register(InAppNotification, InAppNotificationAdmin)
