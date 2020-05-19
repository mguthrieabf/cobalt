import requests
import stripe
import json
import csv
from .forms import TestTransaction, MemberTransfer
from .core import payment_api, update_account, auto_topup_member, get_balance
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import StripeTransaction, MemberTransaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from logs.views import log_event
from django.utils import timezone
from datetime import datetime
from django.db import transaction
from easy_pdf.rendering import render_to_pdf_response
from cobalt.settings import (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY,
                             GLOBAL_MPSERVER, AUTO_TOP_UP_LOW_LIMIT,
                             AUTO_TOP_UP_MIN_AMT, AUTO_TOP_UP_MAX_AMT,
                             AUTO_TOP_UP_DEFAULT_AMT)

####################
# Home             #
####################
@login_required()
def home(request):
    """ Default page.
    """
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

    balance=get_balance(request.user)

    return render(request, 'payments/test_payment.html', {'form': form,
                                                          'auto_amount' : auto_amount,
                                                          'balance': balance,
                                                          'lowbalance': AUTO_TOP_UP_LOW_LIMIT })

####################
# statement_common #
####################
@login_required()
def statement_common(request):
    """ Member statement view - common part across online, pdf and csv
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
    if request.user.auto_amount:
        auto_button = "Auto Top Up Enabled"
    else:
        auto_button = "Add Auto Top Up"

    events_list = MemberTransaction.objects.filter(member=request.user).order_by('-created_date')

    return(summary, club, balance, auto_button, events_list)

#####################
# statement         #
#####################
@login_required()
def statement(request):
    """ Member statement view
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
    """
    (summary, club, balance, auto_button, events_list) = statement_common(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="statement.csv"'

    writer = csv.writer(response)
    writer.writerow([request.user.full_name, request.user.system_number])
    writer.writerow(['Date', 'Reference', 'Type', 'Description', 'Amount', 'Balance'])

    for row in events_list:
        writer.writerow([row.created_date, row.reference_no,
                        row.type, row.description, row.amount, row.balance])

    return response

#####################
# statement_pdf     #
#####################
@login_required()
def statement_pdf(request):
    """ Member statement view - pdf download
    """
    (summary, club, balance, auto_button, events_list) = statement_common(request)

    today = datetime.today().strftime('%-m %B %Y')

    return render_to_pdf_response(request, 'payments/statement_pdf.html', {
                                                        'events': events_list,
                                                        'user': request.user,
                                                        'summary': summary,
                                                        'club': club,
                                                        'balance': balance,
                                                        'today': today})
############################
# Stripe_create_customer   #
############################
@login_required()
def stripe_create_customer(request):
    """ calls Stripe to register a customer
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
    """ view to sign up to auto top up. Creates Stripe customer if not already defined.
        Hands over to Stripe to process card.
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
        except stripe.error.InvalidRequestError as e:
            log_event(user=request.user.full_name,
                      severity="HIGH",
                      source="Payments",
                      sub_source="setup_autotopup",
                      message="Stripe InvalidRequestError: %s" % e.error.message)
            stripe_create_customer(request)
            paylist=None

        except stripe.error.RateLimitError as e:
            log_event(user=request.user.full_name,
                    severity="HIGH",
                    source="Payments",
                    sub_source="setup_autotopup",
                    message="Stripe RateLimitError")

        except stripe.error.AuthenticationError as e:
            log_event(user=request.user.full_name,
                    severity="CRITICAL",
                    source="Payments",
                    sub_source="setup_autotopup",
                    message="Stripe AuthenticationError")

        except stripe.error.APIConnectionError as e:
            log_event(user=request.user.full_name,
                    severity="HIGH",
                    source="Payments",
                    sub_source="setup_autotopup",
                    message="Stripe APIConnectionError - likely network problems")

        except stripe.error.StripeError as e:
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
            with transaction.atomic():
                # Money in
                update_account(member=form.cleaned_data['transfer_to'],
                               other_member=request.user,
                               amount=form.cleaned_data['amount'],
                               description=form.cleaned_data['description'],
                               log_msg="Member Payment Received %s(%s) to %s(%s) $%s" %
                               (request.user.full_name, request.user.system_number,
                                form.cleaned_data['transfer_to'].full_name,
                                form.cleaned_data['transfer_to'].system_number,
                                form.cleaned_data['amount']),
                               source="Payments",
                               sub_source="member_transfer",
                               payment_type="Transfer In"
                               )
                # Money out
                update_account(member=request.user,
                               other_member=form.cleaned_data['transfer_to'],
                               amount=-form.cleaned_data['amount'],
                               description=form.cleaned_data['description'],
                               log_msg="Member Payment Sent %s(%s) to %s(%s) $%s" %
                               (request.user.full_name, request.user.system_number,
                                form.cleaned_data['transfer_to'].full_name,
                                form.cleaned_data['transfer_to'].system_number,
                                form.cleaned_data['amount']),
                               source="Payments",
                               sub_source="member_transfer",
                               payment_type="Transfer Out"
                               )

            msg = "$%s to %s(%s)" % (form.cleaned_data['amount'],
                                     form.cleaned_data['transfer_to'].full_name,
                                     form.cleaned_data['transfer_to'].system_number)
            return render(request, 'payments/member_transfer_successful.html', {"msg": msg})
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

    return render(request, 'payments/member_transfer.html', {'form': form,
                                                             'balance': balance})

########################
# update_auto_amount   #
########################
def update_auto_amount(request):
    """
    Called by the auto top up page when a user changes the amount of the auto top up
    """
    if request.method == "GET":
        amount = request.GET['amount']
        request.user.auto_amount = amount
        request.user.save()
        return HttpResponse("Successful")
