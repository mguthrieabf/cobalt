from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from .models import Balance

@login_required
def home(request):
    return render(request, 'payments/home.html')

def get_balance(system_number):
    try:
        member = Balance.objects.filter(system_number = system_number)
        balance = member[0].balance
        top_date = member[0].last_top_up_date.strftime('%d %b %Y at %-I:%M %p')
        last_top_up = "Last top up %s ($%s)" % (top_date,
                                               member[0].last_top_up_amount)
    except:
        balance = "Not setup"
        last_top_up = "Never"
    return({'balance' : balance, 'last_top_up': last_top_up})
