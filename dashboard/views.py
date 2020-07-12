""" views for dashboard """

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from masterpoints.views import get_masterpoints
from payments.core import get_balance_detail

# from forums.views import post_list_dashboard
from cobalt.utils import cobalt_paginator
from forums.models import Post
from rbac.core import rbac_user_blocked_for_model


@login_required()
def home(request):
    """ Home page """
    system_number = request.user.system_number
    masterpoints = get_masterpoints(system_number)
    payments = get_balance_detail(request.user)
    posts = get_posts(request)

    return render(
        request,
        "dashboard/home.html",
        {"mp": masterpoints, "payments": payments, "posts": posts},
    )


@login_required()
def scroll(request):
    """ Cutdown homepage to be called by infinite scroll.

    Infinite scroll will call this when the user scrolls off the bottom
    of the page. We don't need to update anything except the posts so exclude
    other front page database hits. """

    posts = get_posts(request)
    return render(request, "dashboard/home.html", {"posts": posts})


def get_posts(request):
    """ internal function to get Posts """
    blocked = rbac_user_blocked_for_model(
        user=request.user, app="forums", model="forum", action="view"
    )

    posts_list = Post.objects.exclude(forum__in=blocked).order_by("-created_date")
    posts = cobalt_paginator(request, posts_list, 4)

    return posts
