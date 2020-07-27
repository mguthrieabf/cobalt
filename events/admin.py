from django.contrib import admin
from .models import (
    CongressMaster,
    Congress,
    Event,
    EventEntryType,
    EventEntry,
    EventEntryPlayer,
    CongressNewsItem,
    CongressPeople,
    CongressDownload,
)

admin.site.register(CongressMaster)
admin.site.register(Congress)
admin.site.register(Event)
admin.site.register(EventEntryType)
admin.site.register(EventEntry)
admin.site.register(EventEntryPlayer)
admin.site.register(CongressNewsItem)
admin.site.register(CongressPeople)
admin.site.register(CongressDownload)
