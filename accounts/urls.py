from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('loggedout', views.loggedout, name='loggedout'),
    path('signin', views.loggedout, name='signin'),
    path('search', views.search, name='member_search'),
    path('change_password', views.change_password, name='change_password'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),

]
