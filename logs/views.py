from .models import Log
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from cobalt.settings import DEFAULT_FROM_EMAIL, SUPPORT_EMAIL
from datetime import datetime

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_event(user, severity, source, sub_source, message, request=None):

    if request:
        ip = get_client_ip(request)
    else:
        ip = None

    l = Log()
    l.user = user
    l.ip=ip
    l.severity = severity
    l.source = source
    l.sub_source = sub_source
    l.message = message[:199]
    l.save()

    if severity=="CRITICAL":
        mail_subject = "%s - %s" % (severity, source)
        message = "Severity: %s\nSource: %s\nSub-Source: %s\nUser: %s\nMessage: %s" % (severity,
            source, sub_source, user, message)
        send_mail(mail_subject, message, DEFAULT_FROM_EMAIL, SUPPORT_EMAIL, fail_silently=False)

@user_passes_test(lambda u: u.is_superuser)
def home(request):

    events_list = Log.objects.all().order_by('-event_date')
    page = request.GET.get('page', 1)

    paginator = Paginator(events_list, 10)
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)

    return render(request, 'logs/event_list.html', { 'events': events })
