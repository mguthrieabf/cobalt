from django.conf.urls import url
from . import views

urlpatterns = [
    url('register', views.register, name='register'),
    url('loggedout', views.loggedout, name='loggedout'),
    url('signin', views.loggedout, name='signin'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.activate, name='activate'),
]
