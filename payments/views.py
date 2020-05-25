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
from datetime import datetime
import requests
import stripe
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.db import transaction
from easy_pdf.rendering import render_to_pdf_response
from logs.views import log_event
from cobalt.settings import (STRIPE_SECRET_KEY,
                             GLOBAL_MPSERVER, AUTO_TOP_UP_LOW_LIMIT,
                             AUTO_TOP_UP_DEFAULT_AMT, GLOBAL_CURRENCY_SYMBOL)
from .forms import TestTransaction, MemberTransfer, ManualTopup
from .core import payment_api, update_account, get_balance, auto_topup_member
from .models import MemberTransaction, StripeTransaction
from accounts.models import User

####################
# Home             #
####################
@login_required()
def home(request):
    """ Default page. """

    return render(request, 'payments/home.html')

@login_required()
#################################
# test_payment                  #
#################################
def test_payment(request):
    """This is a temporary view that can be used to test making a payment against
       a members account. This simulates them entering an event or paying a subscription.
"""

    if request.method == 'POST':
        form = TestTransaction(request.POST)
        if form.is_valid():
            description = form.cleaned_data['description']
            amount = form.cleaned_data['amount']
            member = request.user
            organisation = form.cleaned_data['organisation']
            url = form.cleaned_data['url']
            payment_type = form.cleaned_data['type']

            return payment_api(request=request,
                               description=description,
                               amount=amount,
                               member=member,
                               route_code="MAN",
                               route_payload=None,
                               organisation=organisation,
                               log_msg=None,
                               payment_type=payment_type,
                               url=url)
    else:
        form = TestTransaction()

    if request.user.auto_amount:
        auto_amount = request.user.auto_amount
    else:
        auto_amount = None

    balance = get_balance(request.user)

    return render(request, 'payments/test_payment.html', {'form': form,
                                                          'auto_amount' : auto_amount,
                                                          'balance': balance,
                                                          'lowbalance': AUTO_TOP_UP_LOW_LIMIT})

####################
# statement_common #
####################
@login_required()
def statement_common(request):
    """ Member statement view - common part across online, pdf and csv

    Args:
        request - standard request object

    Returns:
        summary - dict of basic info about user from MasterPoints
        club - Home club name
        balance - Users account Balance
        auto_button - text for button (activated or press to setup)
        events_list - list of Member Transactions

    """

# Get summary data
    qry = '%s/mps/%s' % (GLOBAL_MPSERVER, request.user.system_number)
    summary = requests.get(qry).json()[0]

    # Set active to a boolean
    if summary["IsActive"] == "Y":
        summary["IsActive"] = True
    else:
        summary["IsActive"] = False

    # Get home club name
    qry = '%s/club/%s' % (GLOBAL_MPSERVER, summary['HomeClubID'])
    club = requests.get(qry).json()[0]['ClubName']

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

    events_list = MemberTransaction.objects.filter(member=request.user).order_by('-created_date')

    return(summary, club, balance, auto_button, events_list)

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

    page = request.GET.get('page', 1)

    paginator = Paginator(events_list, 30)
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)

    return render(request, 'payments/statement.html', {'events': events,
                                                       'user': request.user,
                                                       'summary': summary,
                                                       'club': club,
                                                       'balance': balance,
                                                       'auto_button': auto_button})

#####################
# statement_csv     #
#####################
@login_required()
def statement_csv(request):
    """ Member statement view - csv download

    Generates a CSV of the statement.

    Args:
        request - standard request object

    Returns:
        HTTPResponse - CSV

    """
    (summary, club, balance, auto_button, events_list) = statement_common(request) # pylint: disable=unused-variable
    today = datetime.today().strftime('%-d %B %Y at %I:%H:%M')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="statement.csv"'

    writer = csv.writer(response)
    writer.writerow([request.user.full_name, request.user.system_number, today])
    writer.writerow(['Date', 'Counterparty', 'Reference', 'Type', 'Description',
                    'Amount', 'Balance'])

    for row in events_list:
        counterparty = ""
        if row.other_member:
            counterparty = row.other_member
        if row.organisation:
            counterparty = row.organisation
        writer.writerow([row.created_date, counterparty, row.reference_no,
                         row.type, row.description, row.amount, row.balance])

    return response

#####################
# statement_pdf     #
#####################
@login_required()
def statement_pdf(request):
    """ Member statement view - csv download

    Generates a PDF of the statement.

    Args:
        request - standard request object

    Returns:
        HTTPResponse - PDF

    """
    (summary, club, balance, auto_button, events_list) = statement_common(request) # pylint: disable=unused-variable

    today = datetime.today().strftime('%-d %B %Y')

    return render_to_pdf_response(request, 'payments/statement_pdf.html',
                                  {
                                      'events': events_list,
                                      'user': request.user,
                                      'summary': summary,
                                      'club': club,
                                      'balance': balance,
                                      'today': today
                                  })
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
        request - a standard request object

    Returns:
        Nothing.

    """
    stripe.api_key = STRIPE_SECRET_KEY
    customer = stripe.Customer.create(metadata={'cobalt_tran_type': 'Auto'})
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
        request - a standard request object

    Returns:
        HTTPResponse

    """
    stripe.api_key = STRIPE_SECRET_KEY
    warn = ""

# Already set up?
    if request.user.stripe_auto_confirmed:
        try:
            paylist = stripe.PaymentMethod.list(
                customer=request.user.stripe_customer_id,
                type="card",
            )
        except stripe.error.InvalidRequestError as error:
            log_event(user=request.user.full_name,
                      severity="HIGH",
                      source="Payments",
                      sub_source="setup_autotopup",
                      message="Stripe InvalidRequestError: %s" % error.error.message)
            stripe_create_customer(request)
            paylist = None

        except stripe.error.RateLimitError:
            log_event(user=request.user.full_name,
                      severity="HIGH",
                      source="Payments",
                      sub_source="setup_autotopup",
                      message="Stripe RateLimitError")

        except stripe.error.AuthenticationError:
            log_event(user=request.user.full_name,
                      severity="CRITICAL",
                      source="Payments",
                      sub_source="setup_autotopup",
                      message="Stripe AuthenticationError")

        except stripe.error.APIConnectionError:
            log_event(user=request.user.full_name,
                      severity="HIGH",
                      source="Payments",
                      sub_source="setup_autotopup",
                      message="Stripe APIConnectionError - likely network problems")

        except stripe.error.StripeError:
            log_event(user=request.user.full_name,
                      severity="CRITICAL",
                      source="Payments",
                      sub_source="setup_autotopup",
                      message="Stripe generic StripeError")

        if paylist:  # if customer has a card associated
            card = paylist.data[0].card
            card_type = card.brand
            card_exp_month = card.exp_month
            card_exp_year = card.exp_year
            card_last4 = card.last4
            warn = f"This will override your {card_type} card ending in {card_last4} \
                    with expiry {card_exp_month}/{card_exp_year}"

    else:
        stripe_create_customer(request)

    return render(request, 'payments/autotopup.html', {'warn': warn})


#######################
# member_transfer     #
#######################
@login_required()
def member_transfer(request):
    """ view to transfer $ to another member

    This view allows a member to transfer money to another member.

    Args:
        Request - standard request object

    Returns:
        HTTPResponse

    """

    msg = ""

    if request.method == 'POST':
        form = MemberTransfer(request.POST, user=request.user)
        if form.is_valid():
            print("member_transfer - about to call")
            return payment_api(request=request, description=form.cleaned_data['description'],
                        amount=form.cleaned_data['amount'], member=request.user,
                        other_member=form.cleaned_data['transfer_to'],
                        payment_type="Pay a Friend")

            # with transaction.atomic():
            #     # Money in
            #     update_account(member=form.cleaned_data['transfer_to'],
            #                    other_member=request.user,
            #                    amount=form.cleaned_data['amount'],
            #                    description=form.cleaned_data['description'],
            #                    log_msg="Member Payment Received %s(%s) to %s(%s) $%s" %
            #                    (request.user.full_name, request.user.system_number,
            #                     form.cleaned_data['transfer_to'].full_name,
            #                     form.cleaned_data['transfer_to'].system_number,
            #                     form.cleaned_data['amount']),
            #                    source="Payments",
            #                    sub_source="member_transfer",
            #                    payment_type="Transfer In"
            #                    )
            #     # Money out
            #     update_account(member=request.user,
            #                    other_member=form.cleaned_data['transfer_to'],
            #                    amount=-form.cleaned_data['amount'],
            #                    description=form.cleaned_data['description'],
            #                    log_msg="Member Payment Sent %s(%s) to %s(%s) $%s" %
            #                    (request.user.full_name, request.user.system_number,
            #                     form.cleaned_data['transfer_to'].full_name,
            #                     form.cleaned_data['transfer_to'].system_number,
            #                     form.cleaned_data['amount']),
            #                    source="Payments",
            #                    sub_source="member_transfer",
            #                    payment_type="Transfer Out"
            #                    )
            #
            # msg = "You transferred %s%s to %s(%s)" % (GLOBAL_CURRENCY_SYMBOL,
            #                          form.cleaned_data['amount'],
            #                          form.cleaned_data['transfer_to'].full_name,
            #                          form.cleaned_data['transfer_to'].system_number)
            # messages.success(request, msg,
            #                  extra_tags='cobalt-message-success')
            # return redirect("payments:payments")
    else:
        form = MemberTransfer(user=request.user)

    # get balance
    last_tran = MemberTransaction.objects.filter(member=request.user).last()
    if last_tran:
        balance = last_tran.balance
    else:
        balance = "Nil"

    recents = MemberTransaction.objects.filter(member=request.user).exclude(other_member=None).values('other_member').distinct()
    recent_transfer_to=[]
    for r in recents:
        member = User.objects.get(pk=r['other_member'])
        recent_transfer_to.append(member)
    return render(request, 'payments/member_transfer.html', {'form': form,
                                                             'recents': recent_transfer_to,
                                                             'balance': balance})

########################
# update_auto_amount   #
########################
def update_auto_amount(request):
    """ Called by the auto top up page when a user changes the amount of the auto top up.

    The auto top up page has Stripe code on it so a standard form won't work
    for this. Instead we use a little Ajax code on the page to handle this.

    Args:
        request - a standard request object

    Returns:
        HTTPResponse

    """
    if request.method == "GET":
        amount = request.GET['amount']
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
        request - a standard request object

    Returns:
        HttpResponse

    """

    if request.method == 'POST':
        form = ManualTopup(request.POST)
        if form.is_valid():
            if form.cleaned_data['card_choice'] == "Existing":  # Use Auto
                (return_code, msg) = auto_topup_member(request.user,
                                     topup_required=form.cleaned_data['amount'],
                                     payment_type="Manual Top Up")
                if return_code:  # success
                    messages.success(request, msg,
                                     extra_tags='cobalt-message-success')
                    return redirect("dashboard")
                else: # error
                    messages.error(request, msg,
                                   extra_tags='cobalt-message-error')
            else:  # Use Manual
                trans = StripeTransaction()
                trans.description = "Manual Top Up"
                trans.amount = form.cleaned_data['amount']
                trans.member = request.user
                trans.save()
                msg = "Manual Top Up - Checkout"
                return render(request, 'payments/checkout.html', {'trans': trans,
                                                                  'msg': msg})
        # else:
        #     print(form.errors)

    else:
        form = ManualTopup()

    return render(request, 'payments/manual_topup.html', {'form': form})

######################
# cancel_auto_top_up #
######################
def cancel_auto_top_up(request):
    """ Cancel auto top up.

    Args:
        request - standard request object

    Returns:
        HTTPResponse
    """

    if request.method == 'POST':
        if request.POST.get("stop_auto"):
            request.user.auto_amount = None
            request.user.stripe_auto_confirmed = None
            request.user.stripe_customer_id = None
            request.user.save()

            messages.info(request, "Auto top up disabled",
                          extra_tags='cobalt-message-success')
            return redirect("payments:payments")
        else:
            return redirect("payments:payments")

    return render(request, 'payments/cancel_autotopup.html')
