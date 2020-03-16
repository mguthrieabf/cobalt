from django.urls import path
from . import views

urlpatterns = [
    path('', views.masterpoints_detail, name='masterpoints'),
    path('view/<int:system_number>/', views.masterpoints_detail, name='masterpoints_detail'),
    path('abf_lookup', views.abf_lookup, name='abf_lookup'),
    path('masterpoints_search', views.masterpoints_search, name='masterpoints_search'),
]
