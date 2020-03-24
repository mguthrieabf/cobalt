from .models import Log
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

def log_event(user, severity, source, sub_source, message):

    l = Log()
    l.user = user
    l.severity = severity
    l.source = source
    l.sub_source = sub_source
    l.message = message
    l.save()

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

# Add styles to rows
    # print(type(events))
    # new_events=[]
    # for event in events:
    #     if event["severity"] == "INFO":
    #         event["css"]="bg-primary text-white"
    #     else:
    #         event["css"]=""
    #     new_events.append(event)

    return render(request, 'logs/event_list.html', { 'events': events })
