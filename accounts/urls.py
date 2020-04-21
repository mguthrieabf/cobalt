from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('loggedout', views.loggedout, name='loggedout'),
    path('signin', views.loggedout, name='signin'),
    path('search', views.search, name='member_search'),
    path('change_password', views.change_password, name='change_password'),
#    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.activate, name='activate'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),

]
