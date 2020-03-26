from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from masterpoints.views import get_masterpoints
from payments.views import get_balance
from accounts.models import User

@login_required(login_url='/accounts/login/')
def home(request):
    system_number = request.user.abf_number
    mp = get_masterpoints(system_number)
    payments = get_balance(request.user)
    return render(request, 'dashboard/home.html', {'mp': mp, 'payments': payments})
