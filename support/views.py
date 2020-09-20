from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from cobalt.settings import ADMINS, COBALT_HOSTNAME
from accounts.models import User
from notifications.views import send_cobalt_email
from django.template.loader import render_to_string
from forums.models import Post
from forums.filters import PostFilter
from utils.utils import cobalt_paginator
from django.db.models import Q
from itertools import chain
import json


@login_required
def home(request):

    return render(request, "support/home.html")


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

    query = request.POST.get("search_string")

    people = User.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    )
    posts = Post.objects.filter(title__icontains=query)

    results = list(chain(people, posts))
    things = cobalt_paginator(request, results)

    return render(request, "support/search.html", {"things": things},)
