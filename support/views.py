from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from cobalt.settings import ADMINS, COBALT_HOSTNAME
from accounts.models import User
from notifications.views import send_cobalt_email
from django.template.loader import render_to_string
from forums.models import Post, Forum
from events.models import Congress
from forums.filters import PostFilter
from payments.models import MemberTransaction
from utils.utils import cobalt_paginator
from django.db.models import Q
from itertools import chain
import json


@login_required
def home(request):

    return render(request, "support/home.html")


def cookies(request):
    return render(request, "support/cookies.html")


def guidelines(request):
    return render(request, "support/guidelines.html")


def acceptable_use(request):
    return render(request, "support/acceptable_use.html")


@login_required
@csrf_exempt
def browser_errors(request):
    """ receive errors from browser code and notify support """

    if request.method == "POST":
        data = request.POST.get("data", None)
        if data:
            errors = json.loads(data)
            print(errors)
            msg = f"""
                  <table>
                      <tr><td>Error<td>{errors['message']}</tr>
                      <tr><td>Line Number<td>{errors['num']}</tr>
                      <tr><td>Page<td>{errors['url']}</tr>
                      <tr><td>User<td>{request.user}</tr>
                  </table>
            """

            for admin in ADMINS:

                context = {
                    "name": admin[0].split()[0],
                    "title": "Some user broke a page again",
                    "email_body": msg,
                    "host": COBALT_HOSTNAME,
                    "link_text": "Set Up Card",
                }

                html_msg = render_to_string(
                    "notifications/email-notification-no-button-error.html", context
                )

                send_cobalt_email(
                    admin[1], f"{COBALT_HOSTNAME} - Client-side Error", html_msg
                )

    return HttpResponse("ok")


@login_required
def search(request):

    query = request.GET.get("search_string")
    include_people = request.GET.get("include_people")
    include_forums = request.GET.get("include_forums")
    include_posts = request.GET.get("include_posts")
    include_events = request.GET.get("include_events")
    include_payments = request.GET.get("include_payments")

    searchparams = ""

    if query:  # don't search if no search string

        searchparams = f"search_string={query}&"

        # Users
        if include_people:
            people = User.objects.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )
            searchparams += "include_people=1&"
        else:
            people = []

        if include_posts:
            posts = Post.objects.filter(title__icontains=query)
            searchparams += "include_posts=1&"
        else:
            posts = []

        if include_forums:
            forums = Forum.objects.filter(title__icontains=query)
            searchparams += "include_forums=1&"
        else:
            forums = []

        if include_events:
            events = Congress.objects.filter(name__icontains=query)
            searchparams += "include_events=1&"
        else:
            events = []

        if include_payments:
            payments = MemberTransaction.objects.filter(description__icontains=query)
            searchparams += "include_payments=1&"
        else:
            payments = []

        # combine outputs
        results = list(chain(people, posts, forums, events, payments))

        # create paginator
        things = cobalt_paginator(request, results)

    else:  # no search string provided

        things = []

    return render(
        request,
        "support/search.html",
        {
            "things": things,
            "search_string": query,
            "include_people": include_people,
            "include_forums": include_forums,
            "include_posts": include_posts,
            "include_events": include_events,
            "include_payments": include_payments,
            "searchparams": searchparams,
        },
    )
