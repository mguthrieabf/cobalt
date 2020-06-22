""" views for dashboard """

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from masterpoints.views import get_masterpoints
from payments.core import get_balance_detail
from forums.views import post_list_dashboard


@login_required()
def home(request):
    """ Home page """
    system_number = request.user.system_number
    masterpoints = get_masterpoints(system_number)
    payments = get_balance_detail(request.user)
    posts = post_list_dashboard(request)
    return render(
        request,
        "dashboard/home.html",
        {"mp": masterpoints, "payments": payments, "posts": posts},
    )
