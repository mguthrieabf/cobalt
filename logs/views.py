from .models import Log
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

def log_event(user, severity, source, sub_source, message):

    l = Log()
    l.user = user
    l.severity = severity
    l.source = source
    l.sub_source = sub_source
    l.message = message
    l.save()

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
