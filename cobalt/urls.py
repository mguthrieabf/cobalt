from django.contrib import admin
from django.urls import path, include
#from dashboard import views
#from results import views

urlpatterns = [
    path('admin/', admin.site.urls),
#    path('', dashboard.views.home, name='home'),
#    path('dashboard/', dashboard.views.home, name='dashboard'),
#    path('results/', results.views.home, name='results'),
    path('dashboard', include('dashboard.urls')),
    path('results', include('results.urls')),

]
