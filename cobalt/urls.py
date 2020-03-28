from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('dashboard', include('dashboard.urls')),
    path('results', include('results.urls')),
    path('accounts', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('calendar', include('calendar_app.urls')),
    path('events', include('events.urls')),
    path('forums', include('forums.urls')),
    path('masterpoints/', include('masterpoints.urls')),
    path('payments/', include('payments.urls')),
    path('logs/', include('logs.urls')),
    path('support', include('support.urls')),
    path('profile', include('user_profile.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
