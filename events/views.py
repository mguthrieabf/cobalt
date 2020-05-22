from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from notifications.views import Notifications

@login_required()
def home(request):
    n = Notifications()
    notification_list = n.get_notifications_for_user(request.user)
    story= n.get_stories_for_user(request.user)
    return render(request, 'events/home.html', {'notifications': notification_list, 'story': story})
