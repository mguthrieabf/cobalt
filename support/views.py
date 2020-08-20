from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone


@login_required
def home(request):
    return render(request, "support/home.html")


@login_required
def rebuild(request):
    f = open("/tmp/trigger.txt", "w")
    f.write("ok")
    f.close()
    return HttpResponse("Request initiated.")
