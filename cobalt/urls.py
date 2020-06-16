from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Overwrite admin panel defaults
admin.site.site_header = f"{settings.GLOBAL_ORG}Tech Administration"
admin.site.site_title = f"{settings.GLOBAL_ORG} Administration"

urlpatterns = [
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("dashboard", include("dashboard.urls")),
    path("results", include("results.urls", namespace="results")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("calendar", include("calendar_app.urls", namespace="calendar")),
    path("events", include("events.urls", namespace="events")),
    path("forums/", include("forums.urls", namespace="forums")),
    path("notifications/", include("notifications.urls", namespace="notifications")),
    path("masterpoints/", include("masterpoints.urls", namespace="masterpoints")),
    path("payments/", include("payments.urls", namespace="payments")),
    path("rbac/", include("rbac.urls", namespace="rbac")),
    path("logs/", include("logs.urls", namespace="logs")),
    path("support", include("support.urls", namespace="support")),
    path("summernote/", include("django_summernote.urls")),
    path("health/", include("health_check.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
