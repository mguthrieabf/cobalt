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
import pytz
from django.utils import timezone, dateformat
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
    GLOBAL_ORG,
    GLOBAL_CURRENCY_SYMBOL,
    TIME_ZONE,
)
from .forms import (
    TestTransaction,
    MemberTransfer,
    ManualTopup,
    SettlementForm,
    AdjustMemberForm,
    AdjustOrgForm,
)
from .core import (
    payment_api,
    get_balance,
    auto_topup_member,
    update_organisation,
    update_account,
)
from .models import MemberTransaction, StripeTransaction, OrganisationTransaction
from accounts.models import User
from cobalt.utils import cobalt_paginator
from organisations.models import Organisation
from rbac.core import rbac_user_has_role
from rbac.views import rbac_forbidden

####################
# Home             #
####################
# @login_required()
# def home(request):
#     """ Default page.
#
#         Args:
#             request (HTTPRequest): Standard request object
#
#         Returns:
#             httpResponse: webpage
#
#     """
#
#     return render(request, "payments/home.html")


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
def statement_common(user):
    """ Member statement view - common part across online, pdf and csv

    Handles the non-formatting parts of statements.

    Args:
        user (User): standard user object

    Returns:
        5-element tuple containing
            - **summary** (*dict*): Basic info about user from MasterPoints
            - **club** (*str*): Home club name
            - **balance** (*float* or *str*): Users account balance
            - **auto_button** (*bool*): status of auto top up
            - **events_list** (*list*): list of MemberTransactions

    """

    # Get summary data
    qry = "%s/mps/%s" % (GLOBAL_MPSERVER, user.system_number)
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
    last_tran = MemberTransaction.objects.filter(member=user).last()
    if last_tran:
        balance = last_tran.balance
    else:
        balance = "Nil"

    # get auto top up
    if user.stripe_auto_confirmed == "On":
        auto_button = True
    else:
        auto_button = False

    events_list = MemberTransaction.objects.filter(member=user).order_by(
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
    (summary, club, balance, auto_button, events_list) = statement_common(request.user)

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


################################
# statement_admin_view         #
################################
@login_required()
def statement_admin_view(request, member_id):
    """ Member statement view for administrators.

    Basic view of statement showing transactions in a web page. Used by an
    administrator to view a members statement

    Args:
        request - standard request object

    Returns:
        HTTPResponse

    """
    if not rbac_user_has_role(request.user, "payments.global.view"):
        return rbac_forbidden(request, "payments.global.view")

    user = get_object_or_404(User, pk=member_id)
    (summary, club, balance, auto_button, events_list) = statement_common(user)

    things = cobalt_paginator(request, events_list, 30)

    return render(
        request,
        "payments/statement.html",
        {
            "things": things,
            "user": user,
            "summary": summary,
            "club": club,
            "balance": balance,
            "auto_button": auto_button,
            "admin_view": True,
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
        if not rbac_user_has_role(request.user, "payments.global.view"):
            return rbac_forbidden(request, "payments.manage.%s.view" % org_id)

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


#########################
# statement_csv_org     #
#########################
@login_required()
def statement_csv_org(request, org_id):
    """ Organisation statement CSV.

    Args:
        request: standard request object
        org_id: organisation to view

    Returns:
        HTTPResponse: CSV

    """

    organisation = get_object_or_404(Organisation, pk=org_id)

    if not rbac_user_has_role(request.user, "payments.manage.%s.view" % org_id):
        if not rbac_user_has_role(request.user, "payments.global.view"):
            return rbac_forbidden(request, "payments.manage.%s.view" % org_id)

    # get details
    events_list = OrganisationTransaction.objects.filter(
        organisation=organisation
    ).order_by("-created_date")

    local_dt = timezone.localtime(timezone.now(), pytz.timezone(TIME_ZONE))
    today = dateformat.format(local_dt, "Y-m-d H:i:s")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="statement.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [organisation.name, "Downloaded by %s" % request.user.full_name, today]
    )
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
        if row.member:
            counterparty = row.member
        if row.other_organisation:
            counterparty = row.other_organisation

        local_dt = timezone.localtime(row.created_date, pytz.timezone(TIME_ZONE))
        writer.writerow(
            [
                dateformat.format(local_dt, "Y-m-d H:i:s"),
                counterparty,
                row.reference_no,
                row.type,
                row.description,
                row.amount,
                row.balance,
            ]
        )

    return response


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
            if not rbac_user_has_role(request.user, "payments.global.view"):
                return rbac_forbidden(request, "payments.manage.%s.view" % org_id)

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
def statement_csv(request, member_id=None):
    """ Member statement view - csv download

    Generates a CSV of the statement.

    Args:
        request (HTTPRequest): standard request object
        member_id(int): id of member to view, defaults to logged in user

    Returns:
        HTTPResponse: CSV headed response with CSV statement data

    """

    if member_id:
        if not rbac_user_has_role(request.user, "payments.global.view"):
            return rbac_forbidden(request, "payments.global.view")
        member = get_object_or_404(User, pk=member_id)
    else:
        member = request.user

    (summary, club, balance, auto_button, events_list) = statement_common(member)

    local_dt = timezone.localtime(timezone.now(), pytz.timezone(TIME_ZONE))
    today = dateformat.format(local_dt, "Y-m-d H:i:s")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="statement.csv"'

    writer = csv.writer(response)
    writer.writerow([member.full_name, member.system_number, today])
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
        local_dt = timezone.localtime(row.created_date, pytz.timezone(TIME_ZONE))
        writer.writerow(
            [
                dateformat.format(local_dt, "Y-m-d H:i:s"),
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
    if request.user.stripe_auto_confirmed == "On":
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
                payment_type="Member Transfer",
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
@login_required()
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
@login_required()
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
@login_required()
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
            request.user.stripe_auto_confirmed = "Off"
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


###########################
# statement_admin_summary #
###########################
@login_required()
def statement_admin_summary(request):
    """ Main statement page for system administrators

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse
    """

    if not rbac_user_has_role(request.user, "payments.global.view"):
        return rbac_forbidden(request, "payments.global.view")

    # Member summary
    total_members = User.objects.count()
    auto_top_up = User.objects.filter(stripe_auto_confirmed="On").count()
    #    total_balance_members_list = MemberTransaction.objects.distinct("member")
    total_balance_members_list = (
        MemberTransaction.objects.all()
        .order_by("member", "-created_date")
        .distinct("member")
    )
    total_balance_members = 0
    members_with_balances = 0
    for item in total_balance_members_list:
        total_balance_members += item.balance
        if item.balance != 0.0:
            members_with_balances += 1

    # Organisation summary
    total_orgs = Organisation.objects.count()
    #    total_balance_orgs_list = OrganisationTransaction.objects.distinct("organisation")
    total_balance_orgs_list = (
        OrganisationTransaction.objects.all()
        .order_by("organisation", "-created_date")
        .distinct("organisation")
    )
    orgs_with_balances = 0
    total_balance_orgs = 0
    for item in total_balance_orgs_list:
        total_balance_orgs += item.balance
        if item.balance != 0.0:
            orgs_with_balances += 1

    # Stripe Summary
    today = timezone.now()
    ref_date = today - datetime.timedelta(days=30)
    stripe = StripeTransaction.objects.filter(created_date__gte=ref_date).aggregate(
        Sum("amount")
    )

    return render(
        request,
        "payments/statement_admin_summary.html",
        {
            "total_members": total_members,
            "auto_top_up": auto_top_up,
            "total_balance_members": total_balance_members,
            "total_orgs": total_orgs,
            "total_balance_orgs": total_balance_orgs,
            "members_with_balances": members_with_balances,
            "orgs_with_balances": orgs_with_balances,
            "balance": total_balance_orgs + total_balance_members,
            "stripe": stripe,
        },
    )


##############
# settlement #
##############
@login_required()
def settlement(request):
    """ process payments to organisations. This is expected to be a monthly
        activity.

    At certain points in time an administrator will clear out the balances of
    the organisations accounts and transfer actual money to them through the
    banking system. This is not currently possible to do electronically so this
    is a manual process.

    The administrator should use this list to match with the bank transactions and
    then confirm through this view that the payments have been made.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse
    """
    if not rbac_user_has_role(request.user, "payments.global.edit"):
        return rbac_forbidden(request, "payments.global.view")

    # orgs with outstanding balances
    # Django is a bit too clever here so we actually have to include balance=0.0 and filter
    # it in the code, otherwise we get the most recent non-zero balance. There may be
    # a way to do this but I couldn't figure it out.
    orgs = OrganisationTransaction.objects.order_by(
        "organisation", "-created_date"
    ).distinct("organisation")
    org_list = []

    non_zero_orgs = []
    for org in orgs:
        if org.balance != 0.0:
            print(org.balance)
            org_list.append((org.id, org.organisation.name))
            non_zero_orgs.append(org)

    if request.method == "POST":
        form = SettlementForm(request.POST, orgs=org_list)
        if form.is_valid():

            # load balances - Important! Do not get the current balance for an
            # org as this may have changed. Use the list confirmed by the user.
            settlement_ids = form.cleaned_data["settle_list"]
            settlements = OrganisationTransaction.objects.filter(pk__in=settlement_ids)

            trans_list = []
            total = 0.0

            # Remove money from org accounts
            for item in settlements:
                total += float(item.balance)
                trans = update_organisation(
                    organisation=item.organisation,
                    amount=-item.balance,
                    description=f"Settlement from {GLOBAL_ORG}",
                    log_msg=f"Settlement from {GLOBAL_ORG} to {item.organisation}",
                    source="payments",
                    sub_source="settlements",
                    payment_type="Settlement",
                )
                trans_list.append(trans)

            messages.success(
                request,
                "Settlement processed successfully.",
                extra_tags="cobalt-message-success",
            )
            return render(
                request,
                "payments/settlement-complete.html",
                {"trans": trans_list, "total": total},
            )

    else:
        form = SettlementForm(orgs=org_list)

    return render(
        request, "payments/settlement.html", {"orgs": non_zero_orgs, "form": form}
    )


########################
# manual_adjust_member #
########################
@login_required()
def manual_adjust_member(request):
    """ make a manual adjustment on a member account

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse
    """
    if not rbac_user_has_role(request.user, "payments.global.edit"):
        return rbac_forbidden(request, "payments.global.edit")

    if request.method == "POST":
        form = AdjustMemberForm(request.POST)
        if form.is_valid():
            member = form.cleaned_data["member"]
            amount = form.cleaned_data["amount"]
            description = form.cleaned_data["description"]
            update_account(
                member=member,
                amount=amount,
                description=description,
                log_msg="Manual adjustment by %s %s %s"
                % (request.user, member, amount),
                source="payments",
                sub_source="manual_adjust_member",
                payment_type="Manual Adjustment",
                other_member=request.user,
            )
            msg = "Manual adjustment successful. %s adjusted by %s%s" % (
                member,
                GLOBAL_CURRENCY_SYMBOL,
                amount,
            )
            messages.success(request, msg, extra_tags="cobalt-message-success")
            return redirect("payments:statement_admin_summary")

    else:
        form = AdjustMemberForm()

        return render(request, "payments/manual_adjust_member.html", {"form": form})


########################
# manual_adjust_org    #
########################
@login_required()
def manual_adjust_org(request):
    """ make a manual adjustment on an organisation account

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse
    """
    if not rbac_user_has_role(request.user, "payments.global.edit"):
        return rbac_forbidden(request, "payments.global.edit")

    if request.method == "POST":
        form = AdjustOrgForm(request.POST)
        if form.is_valid():
            org = form.cleaned_data["organisation"]
            amount = form.cleaned_data["amount"]
            description = form.cleaned_data["description"]
            update_organisation(
                organisation=org,
                amount=amount,
                description=description,
                log_msg=description,
                source="payments",
                sub_source="manual_adjustment_org",
                payment_type="Manual Adjustment",
                member=request.user,
            )
            msg = "Manual adjustment successful. %s adjusted by %s%s" % (
                org,
                GLOBAL_CURRENCY_SYMBOL,
                amount,
            )
            messages.success(request, msg, extra_tags="cobalt-message-success")
            return redirect("payments:statement_admin_summary")

    else:
        form = AdjustOrgForm()

        return render(request, "payments/manual_adjust_org.html", {"form": form})


##########################
# stripe_webpage_confirm #
##########################
@login_required()
def stripe_webpage_confirm(request, stripe_id):
    """ User has been told by Stripe that transaction went through.

    This is called by the web page after Stripe confirms the transaction is approved.
    Because this originates from the client we do not trust it, but we do move
    the status to Pending unless it is already Confirmed (timing issues).

    Args:
        request(HTTPRequest): stasndard request object
        stripe_id(int):  pk of stripe transaction

    Returns:
        Nothing.
    """

    stripe = get_object_or_404(StripeTransaction, pk=stripe_id)
    if stripe.status == "Intent":
        print("Stripe status is intend - updating")
        stripe.status = "Pending"
        stripe.save()

    return HttpResponse("ok")


############################
# stripe_autotopup_confirm #
############################
@login_required()
def stripe_autotopup_confirm(request):
    """ User has been told by Stripe that auto top up went through.

    This is called by the web page after Stripe confirms that auto top up is approved.
    Because this originates from the client we do not trust it, but we do move
    the status to Pending unless it is already Confirmed (timing issues).

    For manual payments we update the transaction, but for auto top up there is
    no transaction so we record this on the User object.

    Args:
        request(HTTPRequest): stasndard request object

    Returns:
        Nothing.
    """

    if request.user.stripe_auto_confirmed == "Off":
        request.user.stripe_auto_confirmed = "Pending"
        request.user.save()

    return HttpResponse("ok")


############################
# stripe_autotopup_confirm #
############################
@login_required()
def stripe_autotopup_off(request):
    """ Switch off auto top up

    This is called by the web page when a user submits new card details to
    Stripe. This is the latest point that we can turn it off in case the
    user aborts the change.

    Args:
        request(HTTPRequest): stasndard request object

    Returns:
        Nothing.
    """

    request.user.stripe_auto_confirmed = "Off"
    request.user.save()

    return HttpResponse("ok")


######################
# stripe_pending     #
######################
@login_required()
def stripe_pending(request):
    """ Shows any pending stripe transactions.

    Stripe transactions should never really be in a pending state unless
    there is a problem. They go from intent to success usually. The only time
    they will sit in pending is if Stripe is slow to talk to us or there is an
    error.

    Args:
        request (HTTPRequest): standard request object

    Returns:
        HTTPResponse
    """
    if not rbac_user_has_role(request.user, "payments.global.view"):
        return rbac_forbidden(request, "payments.global.view")

    try:
        stripe_latest = StripeTransaction.objects.filter(status="Complete").latest(
            "created_date"
        )
        stripe_manual_pending = StripeTransaction.objects.filter(status="Pending")
        stripe_manual_intent = StripeTransaction.objects.filter(
            status="Intent"
        ).order_by("-created_date")[:20]
        stripe_auto_pending = User.objects.filter(stripe_auto_confirmed="Pending")
    except StripeTransaction.DoesNotExist:
        return HttpResponse("No Stripe data found")

    return render(
        request,
        "payments/stripe_pending.html",
        {
            "stripe_manual_pending": stripe_manual_pending,
            "stripe_manual_intent": stripe_manual_intent,
            "stripe_latest": stripe_latest,
            "stripe_auto_pending": stripe_auto_pending,
        },
    )
