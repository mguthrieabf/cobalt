from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from .models import MasterpointsCopy

@login_required
def home(request):
    number = MasterpointsCopy.objects.count()
    params = {'number' : number}
    return render(request, 'masterpoints/home.html', {'number' : number})

def abf_lookup(request):
    if request.method == "GET":
        abf_number = request.GET['abf_number']
        member = MasterpointsCopy.objects.filter(abf_number = abf_number)
        if member:
            given_name = member[0].given_name
            surname = member[0].surname
            result = "%s %s" % (given_name, surname)
        else:
            result = "Invalid or inactive number"
        return render(request, 'masterpoints/abf_lookup.html', {'result' : result})
