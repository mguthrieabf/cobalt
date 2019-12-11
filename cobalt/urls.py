from django.contrib import admin
from django.urls import path, include
#from dashboard import views
#from results import views

urlpatterns = [
    path('admin/', admin.site.urls),
#    path('', dashboard.views.home, name='home'),
#    path('dashboard/', dashboard.views.home, name='dashboard'),
#    path('results/', results.views.home, name='results'),
    path('', include('dashboard.urls')),
    path('dashboard', include('dashboard.urls')),
    path('results', include('results.urls')),
    path('accounts', include('accounts.urls')),
    path('calendar', include('calendar_app.urls')),
    path('events', include('events.urls')),
    path('forums', include('forums.urls')),
    path('masterpoints', include('masterpoints.urls')),
    path('payments', include('payments.urls')),
    path('support', include('support.urls')),

]
