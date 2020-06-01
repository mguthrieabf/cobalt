from django.contrib import admin
from .models import RBACGroup, RBACUserGroup, RBACGroupRole

admin.site.register(RBACGroup)
admin.site.register(RBACUserGroup)
admin.site.register(RBACGroupRole)
