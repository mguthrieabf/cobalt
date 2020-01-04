from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from .models import MasterpointsCopy, MasterpointDetails

@login_required(login_url='/accounts/login/')
def home(request):
    number = MasterpointsCopy.objects.count()
    # params = {'number' : number}
    return render(request, 'masterpoints/home.html', {'number' : number})

@login_required(login_url='/accounts/login/')
def masterpoints_detail(request,system_number):
    details = MasterpointDetails.objects.filter(system_number = system_number).order_by('-posting_date')[:20]
    summary = MasterpointsCopy.objects.filter(abf_number = system_number)
    print(summary)
    return render(request, 'masterpoints/details.html', {'details' : details, 'summary': summary[0]})




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

def get_masterpoints(abf_number):
    try:
        member = MasterpointsCopy.objects.filter(abf_number = abf_number)
        points = member[0].total_MPs
        rank = member[0].rank
    except:
        points = "Not found"
        rank = "Not found"
    return({'points' : points, 'rank': rank})
