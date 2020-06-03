from django.contrib import admin
from .models import RBACGroup, RBACUserGroup, RBACGroupRole, RBACModelDefault, RBACAppModelAction

admin.site.register(RBACGroup)
admin.site.register(RBACUserGroup)
admin.site.register(RBACGroupRole)
admin.site.register(RBACModelDefault)
admin.site.register(RBACAppModelAction)
