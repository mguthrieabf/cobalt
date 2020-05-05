import requests
import stripe
import json
import csv
from .forms import (OneOffPayment, TestTransaction, TestAutoTopUp,
                    MemberTransfer)
from .core import payment_api, update_account, auto_topup_member
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import (StripeTransaction, MemberTransaction,
                     AutoTopUpConfig)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from logs.views import log_event
from django.utils import timezone
from datetime import datetime
from django.db import transaction
from easy_pdf.rendering import render_to_pdf_response
from cobalt.settings import (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY,
                             GLOBAL_MPSERVER)

####################
# Home             #
####################
@login_required()
def home(request):
    """ Default page.
    :view:`payments.test_payment`
    """
    return render(request, 'payments/home.html')


@login_required()
#################################
# test_payment                  #
#################################
def test_payment(request):
    """This is a temporary view that can be used to test making a payment against
       a members account. This simulates them entering an event or paying a subscription.
       The form takes 4 inputs:

       **Context**
"""

    if request.method == 'POST':
        form = OneOffPayment(request.POST)
        if form.is_valid():
            description = form.cleaned_data['description']
            amount = form.cleaned_data['amount']
            member = request.user
            route_code = form.cleaned_data['route_code']
            route_payload = form.cleaned_data['route_payload']
            return payment_api(request, description, amount, member, route_code, route_payload)
    else:
        form = OneOffPayment()

    return render(request, 'payments/test_payment.html', {'form': form})

###########################
# test_autotopup          #
###########################
@login_required()
def test_autotopup(request):
    """
view for auto top up payments
"""
    if request.method == 'POST':
        form = TestAutoTopUp(request.POST)
        if form.is_valid():

            description = form.cleaned_data['description']
            amount = form.cleaned_data['amount']
            member = form.cleaned_data['payer']

            (rc, msg) = auto_topup_member(member)

            if rc:
                messages.success(request, msg,
                               extra_tags='cobalt-message-success')
            else:
                messages.error(request, msg,
                               extra_tags='cobalt-message-error')

    else:
        form = TestAutoTopUp()

    return render(request, 'payments/test_autotopup.html', {'form': form})

##########################
# test_transaction       #
##########################
@login_required()
def test_transaction(request):
    """ Temporary way to make a change to  $ account """

    log_event(request=request,
              user=request.user.full_name,
              severity="INFO",
              source="Payments",
              sub_source="test_payment",
              message="User went to test transaction screen")

    if request.method == 'POST':
        form = TestTransaction(request.POST)
        if form.is_valid():
            update_account(member=form.cleaned_data['payer'],
                           amount=-form.cleaned_data['amount'],
                           organisation=form.cleaned_data['counterparty'],
                           description=form.cleaned_data['description'],
                           log_msg="Manual Payments Update: $%s %s" %
                           (form.cleaned_data['amount'],
                            form.cleaned_data['description']),
                           source="Payments",
                           sub_source="test_transaction",
                           type="Miscellaneous"
                           )
            messages.success(request,
                             'Transfer complete. %s - $%s' %
                             (form.cleaned_data['payer'], form.cleaned_data['amount']),
                             extra_tags='cobalt-message-success')
            form = TestTransaction()
    else:
        form = TestTransaction()

    return render(request, 'payments/test_transaction.html', {'form': form})

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
    auto_top_up = AutoTopUpConfig.objects.filter(member=request.user)
    if auto_top_up:
        auto_button = "Update Auto Top Up"
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
#######################
# setup_autotopup     #
#######################
@login_required()
def setup_autotopup(request):
    """ view to sign up to auto top up
    """
    stripe.api_key = STRIPE_SECRET_KEY
    warn = ""
# Already a customer?
    autotopup = AutoTopUpConfig.objects.filter(member=request.user).first()
    if autotopup:                           # record exists
        print("auto top up record found")
        if autotopup.stripe_customer_id:    # cust_id exists
            print("Found autotopup with stripe details")
            paylist = stripe.PaymentMethod.list(
              customer=autotopup.stripe_customer_id,
              type="card",
            )
            # TODO This needs to handle invalid customer exception
            card = paylist.data[0].card
            card_type = card.brand
            card_exp_month = card.exp_month
            card_exp_year = card.exp_year
            card_last4 = card.last4
            warn = f"This will override your {card_type} card ending in {card_last4} \
                    with expiry {card_exp_month}/{card_exp_year}"

    else:
        stripe.api_key = STRIPE_SECRET_KEY
        customer = stripe.Customer.create()
        auto = AutoTopUpConfig()
        auto.member = request.user
        auto.stripe_customer_id = customer.id
        auto.auto_amount = 100.0
        auto.save()

    return render(request, 'payments/autotopup.html', {'warn': warn})


#######################
# member_transfer     #
#######################
@login_required()
def member_transfer(request):
    """ view to transfer $ to another member
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
                               type="Transfer In"
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
                               type="Transfer Out"
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
