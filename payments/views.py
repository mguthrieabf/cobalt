# -*- coding: utf-8 -*-
"""Handles all activities associated with payments that talk to users.

This module handles all of the functions that interact directly with
a user. i.e. they generally accept a ``Request`` and return an
``HttpResponse``.
See also `Payments Core`_. This handles the other side of the interactions.
They both work together.

Key Points:
    - Payments is a service module, it is requested to do things on behalf of
      another module and does not know why it is doing them.
    - Payments are often not real time, for manual payments, the user will
      be taken to another screen that interacts directly with Stripe, and for
      automatic top up payments, the top up may fail and require user input.
    - The asynchronous nature of payments makes it more complex than many of
      the Cobalt modules so the documentation needs to be of a higher standard.
      See `Payments Overview`_ for more details.

.. _Payments Core:
   #module-payments.core

.. _Payments Overview:
   ./payments_overview.html

"""

import csv
import datetime
import requests
import stripe
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.db.models import Sum
from django.contrib import messages

# from easy_pdf.rendering import render_to_pdf_response
from logs.views import log_event
from cobalt.settings import (
    STRIPE_SECRET_KEY,
    GLOBAL_MPSERVER,
    AUTO_TOP_UP_LOW_LIMIT,
    AUTO_TOP_UP_DEFAULT_AMT,
)
from .forms import TestTransaction, MemberTransfer, ManualTopup
from .core import payment_api, get_balance, auto_topup_member
from .models import MemberTransaction, StripeTransaction, OrganisationTransaction
from accounts.models import User
from cobalt.utils import cobalt_paginator
from organisations.models import Organisation
from rbac.core import rbac_user_has_role

####################
# Home             #
####################
@login_required()
def home(request):
    """ Default page.

        Args:
            request (HTTPRequest): Standard request object

        Returns:
            httpResponse: webpage

    """

    return render(request, "payments/home.html")


@login_required()
#################################
# test_payment                  #
#################################
def test_payment(request):
    """This is a temporary view that can be used to test making a payment against
       a members account. This simulates them entering an event or paying a subscription.
"""

    if request.method == "POST":
        form = TestTransaction(request.POST)
        if form.is_valid():
            description = form.cleaned_data["description"]
            amount = form.cleaned_data["amount"]
            member = request.user
            organisation = form.cleaned_data["organisation"]
            url = form.cleaned_data["url"]
            payment_type = form.cleaned_data["type"]

            return payment_api(
                request=request,
                description=description,
                amount=amount,
                member=member,
                route_code="MAN",
                route_payload=None,
                organisation=organisation,
                log_msg=None,
                payment_type=payment_type,
                url=url,
            )
    else:
        form = TestTransaction()

    if request.user.auto_amount:
        auto_amount = request.user.auto_amount
    else:
        auto_amount = None

    balance = get_balance(request.user)

    return render(
        request,
        "payments/test_payment.html",
        {
            "form": form,
            "auto_amount": auto_amount,
            "balance": balance,
            "lowbalance": AUTO_TOP_UP_LOW_LIMIT,
        },
    )


####################
# statement_common #
####################
@login_required()
def statement_common(request):
    """ Member statement view - common part across online, pdf and csv

    Handles the non-formatting parts of statements.

    Args:
        request (str): standard request object

    Returns:
        5-element tuple containing
            - **summary** (*dict*): Basic info about user from MasterPoints
            - **club** (*str*): Home club name
            - **balance** (*float* or *str*): Users account balance
            - **auto_button** (*bool*): status of auto top up
            - **events_list** (*list*): list of MemberTransactions

    """

    # Get summary data
    qry = "%s/mps/%s" % (GLOBAL_MPSERVER, request.user.system_number)
    try:
        summary = requests.get(qry).json()[0]
    except IndexError:
        raise Http404

    # Set active to a boolean
    if summary["IsActive"] == "Y":
        summary["IsActive"] = True
    else:
        summary["IsActive"] = False

    # Get home club name
    qry = "%s/club/%s" % (GLOBAL_MPSERVER, summary["HomeClubID"])
    club = requests.get(qry).json()[0]["ClubName"]

    # get balance
    last_tran = MemberTransaction.objects.filter(member=request.user).last()
    if last_tran:
        balance = last_tran.balance
    else:
        balance = "Nil"

    # get auto top up
    if request.user.stripe_auto_confirmed:
        auto_button = True
    else:
        auto_button = False

    events_list = MemberTransaction.objects.filter(member=request.user).order_by(
        "-created_date"
    )

    return (summary, club, balance, auto_button, events_list)


#####################
# statement         #
#####################
@login_required()
def statement(request):
    """ Member statement view.

    Basic view of statement showing transactions in a web page.

    Args:
        request - standard request object

    Returns:
        HTTPResponse

    """
    (summary, club, balance, auto_button, events_list) = statement_common(request)

    things = cobalt_paginator(request, events_list, 30)

    return render(
        request,
        "payments/statement.html",
        {
            "things": things,
            "user": request.user,
            "summary": summary,
            "club": club,
            "balance": balance,
            "auto_button": auto_button,
        },
    )


#####################
# statement_org     #
#####################
@login_required()
def statement_org(request, org_id):
    """ Organisation statement view.

    Basic view of statement showing transactions in a web page.

    Args:
        request: standard request object
        org_id: organisation to view

    Returns:
        HTTPResponse

    """

    organisation = get_object_or_404(Organisation, pk=org_id)

    if not rbac_user_has_role(request.user, "payments.manage.%s.view" % org_id):
        return HttpResponse("Access Denied")

    # get balance
    last_tran = OrganisationTransaction.objects.filter(organisation=organisation).last()
    if last_tran:
        balance = last_tran.balance
    else:
        balance = "Nil"

    # get summary
    today = timezone.now()
    ref_date = today - datetime.timedelta(days=30)
    summary = (
        OrganisationTransaction.objects.filter(
            organisation=organisation, created_date__gte=ref_date
        )
        .values("type")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    total = 0.0
    for item in summary:
        total = total + float(item["total"])

    # get details
    events_list = OrganisationTransaction.objects.filter(
        organisation=organisation
    ).order_by("-created_date")

    things = cobalt_paginator(request, events_list, 30)

    return render(
        request,
        "payments/statement_org.html",
        {
            "things": things,
            "balance": balance,
            "org": organisation,
            "summary": summary,
            "total": total,
        },
    )


def statement_org_summary_ajax(request, org_id, range):
    """ Called by the org statement when the summary date range changes

    Args:
        request (HTTPRequest): standard request object
        org_id(int): pk of the org to query
        range(str): range to include in summary

    Returns:
        HTTPResponse: data for table

    """
    if request.method == "GET":

        organisation = get_object_or_404(Organisation, pk=org_id)

        if not rbac_user_has_role(request.user, "payments.manage.%s.view" % org_id):
            return HttpResponse("Access Denied")

        if range == "All":
            summary = (
                OrganisationTransaction.objects.filter(organisation=organisation)
                .values("type")
                .annotate(total=Sum("amount"))
                .order_by("-total")
            )
        else:
            days = int(range)
            today = timezone.now()
            ref_date = today - datetime.timedelta(days=days)
            summary = (
                OrganisationTransaction.objects.filter(
                    organisation=organisation, created_date__gte=ref_date
                )
                .values("type")
                .annotate(total=Sum("amount"))
                .order_by("-total")
            )

    total = 0.0
    for item in summary:
        total = total + float(item["total"])

    return render(
        request,
        "payments/statement_org_summary_ajax.html",
        {"summary": summary, "total": total},
    )


#####################
# statement_csv     #
#####################
@login_required()
def statement_csv(request):
    """ Member statement view - csv download

    Generates a CSV of the statement.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse: CSV headed response with CSV statement data

    """
    (summary, club, balance, auto_button, events_list) = statement_common(
        request
    )  # pylint: disable=unused-variable
    today = datetime.today().strftime("%-d %B %Y at %I:%H:%M")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="statement.csv"'

    writer = csv.writer(response)
    writer.writerow([request.user.full_name, request.user.system_number, today])
    writer.writerow(
        [
            "Date",
            "Counterparty",
            "Reference",
            "Type",
            "Description",
            "Amount",
            "Balance",
        ]
    )

    for row in events_list:
        counterparty = ""
        if row.other_member:
            counterparty = row.other_member
        if row.organisation:
            counterparty = row.organisation
        writer.writerow(
            [
                row.created_date,
                counterparty,
                row.reference_no,
                row.type,
                row.description,
                row.amount,
                row.balance,
            ]
        )

    return response


#####################
# statement_pdf     #
#####################
@login_required()
def statement_pdf(request):
    """ Member statement view - csv download

    Generates a PDF of the statement.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse: PDF headed response with PDF statement data


    """
    #    (summary, club, balance, auto_button, events_list) = statement_common(
    #        request
    #    )  # pylint: disable=unused-variable

    #    today = datetime.today().strftime("%-d %B %Y")

    # return render_to_pdf_response(
    #     request,
    #     "payments/statement_pdf.html",
    #     {
    #         "events": events_list,
    #         "user": request.user,
    #         "summary": summary,
    #         "club": club,
    #         "balance": balance,
    #         "today": today,
    #     },
    # )

    return


############################
# Stripe_create_customer   #
############################
@login_required()
def stripe_create_customer(request):
    """ calls Stripe to register a customer.

    Creates a new customer entry with Stripe and sets this member's
    stripe_customer_id to match the customer created. Also sets the
    auto_amount for the member to the system default.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        Nothing.
    """

    stripe.api_key = STRIPE_SECRET_KEY
    customer = stripe.Customer.create(metadata={"cobalt_tran_type": "Auto"})
    request.user.stripe_customer_id = customer.id
    request.user.auto_amount = AUTO_TOP_UP_DEFAULT_AMT
    request.user.save()


#######################
# setup_autotopup     #
#######################
@login_required()
def setup_autotopup(request):
    """ view to sign up to auto top up.

    Creates Stripe customer if not already defined.
    Hands over to Stripe to process card.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse: Our page with Stripe code embedded.

    """
    stripe.api_key = STRIPE_SECRET_KEY
    warn = ""

    # Already set up?
    if request.user.stripe_auto_confirmed:
        try:
            paylist = stripe.PaymentMethod.list(
                customer=request.user.stripe_customer_id, type="card",
            )
        except stripe.error.InvalidRequestError as error:
            log_event(
                user=request.user.full_name,
                severity="HIGH",
                source="Payments",
                sub_source="setup_autotopup",
                message="Stripe InvalidRequestError: %s" % error.error.message,
            )
            stripe_create_customer(request)
            paylist = None

        except stripe.error.RateLimitError:
            log_event(
                user=request.user.full_name,
                severity="HIGH",
                source="Payments",
                sub_source="setup_autotopup",
                message="Stripe RateLimitError",
            )

        except stripe.error.AuthenticationError:
            log_event(
                user=request.user.full_name,
                severity="CRITICAL",
                source="Payments",
                sub_source="setup_autotopup",
                message="Stripe AuthenticationError",
            )

        except stripe.error.APIConnectionError:
            log_event(
                user=request.user.full_name,
                severity="HIGH",
                source="Payments",
                sub_source="setup_autotopup",
                message="Stripe APIConnectionError - likely network problems",
            )

        except stripe.error.StripeError:
            log_event(
                user=request.user.full_name,
                severity="CRITICAL",
                source="Payments",
                sub_source="setup_autotopup",
                message="Stripe generic StripeError",
            )

        if paylist:  # if customer has a card associated
            card = paylist.data[0].card
            card_type = card.brand
            card_exp_month = card.exp_month
            card_exp_year = card.exp_year
            card_last4 = card.last4
            warn = f"Changing card details will override your {card_type} card ending in {card_last4} \
                    with expiry {card_exp_month}/{card_exp_year}"

    else:
        stripe_create_customer(request)

    balance = get_balance(request.user)
    topup = request.user.auto_amount

    return render(
        request,
        "payments/autotopup.html",
        {"warn": warn, "topup": topup, "balance": balance},
    )


#######################
# member_transfer     #
#######################
@login_required()
def member_transfer(request):
    """ view to transfer $ to another member

    This view allows a member to transfer money to another member.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse

    """

    if request.method == "POST":
        form = MemberTransfer(request.POST, user=request.user)
        if form.is_valid():
            print("member_transfer - about to call")
            return payment_api(
                request=request,
                description=form.cleaned_data["description"],
                amount=form.cleaned_data["amount"],
                member=request.user,
                other_member=form.cleaned_data["transfer_to"],
                payment_type="Pay a Friend",
            )
        else:
            print(form.errors)
    else:
        form = MemberTransfer(user=request.user)

    # get balance
    last_tran = MemberTransaction.objects.filter(member=request.user).last()
    if last_tran:
        balance = last_tran.balance
    else:
        balance = "Nil"

    recents = (
        MemberTransaction.objects.filter(member=request.user)
        .exclude(other_member=None)
        .values("other_member")
        .distinct()
    )
    recent_transfer_to = []
    for r in recents:
        member = User.objects.get(pk=r["other_member"])
        recent_transfer_to.append(member)
    return render(
        request,
        "payments/member_transfer.html",
        {"form": form, "recents": recent_transfer_to, "balance": balance},
    )


########################
# update_auto_amount   #
########################
def update_auto_amount(request):
    """ Called by the auto top up page when a user changes the amount of the auto top up.

    The auto top up page has Stripe code on it so a standard form won't work
    for this. Instead we use a little Ajax code on the page to handle this.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse: "Successful"

    """
    if request.method == "GET":
        amount = request.GET["amount"]
        request.user.auto_amount = amount
        request.user.save()

    return HttpResponse("Successful")


###################
# manual_topup    #
###################
def manual_topup(request):
    """ Page to allow credit card top up regardless of auto status.

    This page allows a member to add to their account using a credit card,
    they can do this even if they have already set up for auto top up.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse

    """

    if request.method == "POST":
        form = ManualTopup(request.POST)
        if form.is_valid():
            if form.cleaned_data["card_choice"] == "Existing":  # Use Auto
                (return_code, msg) = auto_topup_member(
                    request.user,
                    topup_required=form.cleaned_data["amount"],
                    payment_type="Manual Top Up",
                )
                if return_code:  # success
                    messages.success(request, msg, extra_tags="cobalt-message-success")
                    return redirect("payments:payments")
                else:  # error
                    messages.error(request, msg, extra_tags="cobalt-message-error")
            else:  # Use Manual
                trans = StripeTransaction()
                trans.description = "Manual Top Up"
                trans.amount = form.cleaned_data["amount"]
                trans.member = request.user
                trans.save()
                msg = "Manual Top Up - Checkout"
                return render(
                    request, "payments/checkout.html", {"trans": trans, "msg": msg}
                )
        # else:
        #     print(form.errors)

    else:
        form = ManualTopup()

    balance = get_balance(request.user)

    return render(
        request, "payments/manual_topup.html", {"form": form, "balance": balance}
    )


######################
# cancel_auto_top_up #
######################
def cancel_auto_top_up(request):
    """ Cancel auto top up.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse
    """

    if request.method == "POST":
        if request.POST.get("stop_auto"):
            request.user.auto_amount = None
            request.user.stripe_auto_confirmed = None
            request.user.stripe_customer_id = None
            request.user.save()

            messages.info(
                request, "Auto top up disabled", extra_tags="cobalt-message-success"
            )
            return redirect("payments:payments")
        else:
            return redirect("payments:payments")

    balance = get_balance(request.user)
    return render(request, "payments/cancel_autotopup.html", {"balance": balance})
