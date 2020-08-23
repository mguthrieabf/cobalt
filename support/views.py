from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from notifications.views import send_cobalt_email
from cobalt.settings import COBALT_HOSTNAME

# from django.http import HttpResponse
# from django.utils import timezone


@login_required
def home(request):
    return render(request, "support/home.html")


@login_required
def rebuild(request):
    f = open("/tmp/trigger.txt", "w")
    f.write("ok")
    f.close()
    send_cobalt_email('m@rkguthrie.com', 'Test Data Reset on %s by %s' % (COBALT_HOSTNAME, request.user.first_name), " ")
    return render(request, "support/rebuild.html")
