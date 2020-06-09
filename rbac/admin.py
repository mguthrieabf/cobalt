from django.contrib import admin
from .models import (
    RBACGroup,
    RBACUserGroup,
    RBACGroupRole,
    RBACAdminGroup,
    RBACAdminUserGroup,
    RBACAdminGroupRole,
    RBACModelDefault,
    RBACAppModelAction,
)

admin.site.register(RBACGroup)
admin.site.register(RBACUserGroup)
admin.site.register(RBACGroupRole)
admin.site.register(RBACAdminGroup)
admin.site.register(RBACAdminUserGroup)
admin.site.register(RBACAdminGroupRole)
admin.site.register(RBACModelDefault)
admin.site.register(RBACAppModelAction)
