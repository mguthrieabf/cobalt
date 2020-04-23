from django.urls import path
from . import views
from django.http import HttpResponse

urlpatterns = [
    path('register', views.register, name='register'),
    path('loggedout', views.loggedout, name='loggedout'),
    path('signin', views.loggedout, name='signin'),
    path('search', views.search, name='member_search'),
    path('change-password', views.change_password, name='change_password'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),
    path('profile', views.profile, name='user_profile'),
    path('update-blurb', views.blurb_form_upload, name='user_blurb'),
    path('public-profile/<int:pk>/', views.public_profile, name='public_profile'),
]

def not_found_handler(request, exception=None):
    return HttpResponse('Error handler content', status=403)

handler404 = not_found_handler
