from django.contrib import admin
from .models import User

class UserAdmin(admin.ModelAdmin):
    search_fields = ('last_name', 'system_number')

admin.site.register(User, UserAdmin)
