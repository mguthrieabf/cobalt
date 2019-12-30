from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from masterpoints.views import get_masterpoints

@login_required(login_url='/accounts/login/')
def home(request):
    mp = get_masterpoints('620254')
    print(mp)
    return render(request, 'dashboard/home.html', {'mp': mp})
