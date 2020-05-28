from django.contrib import admin
from .models import InAppNotification, NotificationMapping

class InAppNotificationAdmin(admin.ModelAdmin):
    search_fields = ('member',)

class NotificationMappingAdmin(admin.ModelAdmin):
    search_fields = ('member',)

admin.site.register(InAppNotification, InAppNotificationAdmin)
admin.site.register(NotificationMapping, NotificationMappingAdmin)
