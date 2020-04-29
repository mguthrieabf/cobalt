from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Balance, StripeTransaction, MemberTransaction, AutoTopUpConfig
from .forms import OneOffPayment, TestTransaction, TestAutoTopUp, MemberTransfer
from .core import payment_api, update_account
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from logs.views import log_event
from django.utils import timezone
import requests
import stripe
import json
import csv
from datetime import datetime
from easy_pdf.rendering import render_to_pdf_response
from cobalt.settings import STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, GLOBAL_MPSERVER

####################
# Home             #
####################
@login_required(login_url='/accounts/login/')
def home(request):
    """ Default page """
    return render(request, 'payments/home.html')

@login_required(login_url='/accounts/login/')
#################################
# test_payment                  #
#################################
def test_payment(request):
    """view for simple payments
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
@login_required(login_url='/accounts/login/')
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

            autotopup = AutoTopUpConfig.objects.filter(member=member).first()

            if not autotopup:
                messages.error(request, "Auto Top Up, not set up for this user.", extra_tags='cobalt-message-error')

                log_event(request = request,
                          user = request.user.full_name,
                          severity = "WARN",
                          source = "Payments",
                          sub_source = "test_autotopup",
                          message = "user not set up for auto top up %s" % member)

                return render(request, 'payments/test_autotopup.html', {'form': form})

            stripe.api_key = STRIPE_SECRET_KEY

# Get payment method id for this customer from Stripe
            try:
                paylist = stripe.PaymentMethod.list(
                  customer=autotopup.stripe_customer_id,
                  type="card",
                )
                pay_method_id = paylist.data[0].id
            except InvalidRequestError:
                messages.error(request, "Oops. Problem with payment.", extra_tags='cobalt-message-error')

                log_event(request = request,
                          user = request.user.full_name,
                          severity = "WARN",
                          source = "Payments",
                          sub_source = "test_autotopup",
                          message = "Error from stripe - see logs")

                return render(request, 'payments/test_autotopup.html', {'form': form})

# try payment
            try:
                rc=stripe.PaymentIntent.create(
                amount = amount * 100,
                currency = 'aud',
                customer = autotopup.stripe_customer_id,
                payment_method = pay_method_id,
                off_session = True,
                confirm = True,
                )

                print(rc)

# It worked so create a stripe record
                payload  = rc.charges.data[0]

                pi_reference    = payload.id
                pi_method       = payload.payment_method
                pi_amount       = payload.amount
                pi_currency     = payload.currency
                pi_receipt_url  = payload.receipt_url
                pi_brand        = payload.payment_method_details.card.brand
                pi_country      = payload.payment_method_details.card.country
                pi_exp_month    = payload.payment_method_details.card.exp_month
                pi_exp_year     = payload.payment_method_details.card.exp_year
                pi_last4        = payload.payment_method_details.card.last4

                stripe_tran = StripeTransaction()
                stripe_tran.description = f"Auto top up for {member.full_name} ({member.system_number})"
                stripe_tran.amount = amount
                stripe_tran.member = member
                stripe_tran.route_code = None
                stripe_tran.route_payload = None
                stripe_tran.stripe_reference = pi_reference
                stripe_tran.stripe_method = pi_method
                stripe_tran.stripe_currency = pi_currency
                stripe_tran.stripe_receipt_url = pi_receipt_url
                stripe_tran.stripe_brand = pi_brand
                stripe_tran.stripe_country = pi_country
                stripe_tran.stripe_exp_month = pi_exp_month
                stripe_tran.stripe_exp_year = pi_exp_year
                stripe_tran.stripe_last4 = pi_last4
                stripe_tran.last_change_date = timezone.now()
                stripe_tran.status = "Complete"
                stripe_tran.save()

# Update members account
                update_account(member = member,
                             amount = amount,
                             description = "Auto Top Up",
                             log_msg = "$%s Auto Top Up" % amount,
                             source = "Payments",
                             sub_source = "auto_top_up",
                             type = "Auto Top Up",
                             stripe_transaction = stripe_tran
                             )

                messages.success(request, 'Success!: Auto top up successful. $%s' % form.cleaned_data['amount'], extra_tags='cobalt-message-success')
                form = TestAutoTopUp()

            except stripe.error.CardError as e:
                err = e.error
                # Error code will be authentication_required if authentication is needed
                log_event(request = request,
                          user = request.user.full_name,
                          severity = "WARN",
                          source = "Payments",
                          sub_source = "test_autotopup",
                          message = "Error from stripe - see logs")

                messages.error(request, 'Error!: Stripe error code: %s' % err.code, extra_tags='cobalt-message-error')

                print("Code is: %s" % err.code)
                payment_intent_id = err.payment_intent['id']
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

#            return payment_api(request, description, amount, member, route_code, route_payload)
    else:
        form = TestAutoTopUp()

    return render(request, 'payments/test_autotopup.html', {'form': form})

##########################
# test_transaction       #
##########################
@login_required(login_url='/accounts/login/')
def test_transaction(request):
    """ Temporary way to make a change to  $ account """

    log_event(request = request,
              user = request.user.full_name,
              severity = "INFO",
              source = "Payments",
              sub_source = "test_payment",
              message = "User went to test transaction screen")

    if request.method == 'POST':
        form = TestTransaction(request.POST)
        if form.is_valid():
            update_account(member = form.cleaned_data['payer'],
                           amount = -form.cleaned_data['amount'],
                           organisation = form.cleaned_data['counterparty'],
                           description = form.cleaned_data['description'],
                           log_msg = "Manual Payments Update: $%s %s" %
                               (form.cleaned_data['amount'], form.cleaned_data['description']),
                           source = "Payments",
                           sub_source = "test_transaction",
                           type = "Miscellaneous"
                           )
            messages.success(request, 'Transfer complete. %s - $%s' % (form.cleaned_data['payer'], form.cleaned_data['amount']), extra_tags='cobalt-message-success')
            form = TestTransaction()
    else:
        form = TestTransaction()

    return render(request, 'payments/test_transaction.html', {'form': form})

####################
# statement_common #
####################
@login_required(login_url='/accounts/login/')
def statement_common(request):
    """ Member statement view - common part across online, pdf and csv
    """

# Get summary data
    qry = '%s/mps/%s' % (GLOBAL_MPSERVER, request.user.system_number)
    summary = requests.get(qry).json()[0]

    # Set active to a boolean
    if summary["IsActive"]=="Y":
        summary["IsActive"]=True
    else:
        summary["IsActive"]=False

    # Get home club name
    qry = '%s/club/%s' % (GLOBAL_MPSERVER, summary['HomeClubID'])
    club = requests.get(qry).json()[0]['ClubName']

    # get balance
    try:
        balance_inst = Balance.objects.filter(member=request.user)[0]
        balance = balance_inst.balance
    except IndexError:
        balance = "Nil"

    # get auto top up
    auto_top_up = AutoTopUpConfig.objects.filter(member = request.user)
    if auto_top_up:
        auto_button = "Update Auto Top Up"
    else:
        auto_button = "Add Auto Top Up"

    events_list = MemberTransaction.objects.filter(member=request.user).order_by('-created_date')

    return(summary, club, balance, auto_button, events_list)

#####################
# statement         #
#####################
@login_required(login_url='/accounts/login/')
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

    return render(request, 'payments/statement.html', { 'events': events,
                                                        'user': request.user,
                                                        'summary': summary,
                                                        'club': club,
                                                        'balance': balance,
                                                        'auto_button': auto_button})

#####################
# statement_csv     #
#####################
@login_required(login_url='/accounts/login/')
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
@login_required(login_url='/accounts/login/')
def statement_pdf(request):
    """ Member statement view - pdf download
    """
    (summary, club, balance, auto_button, events_list) = statement_common(request)

    today = datetime.today().strftime('%-m %B %Y')

    return render_to_pdf_response(request, 'payments/statement_pdf.html', { 'events': events_list,
                                                        'user': request.user,
                                                        'summary': summary,
                                                        'club': club,
                                                        'balance': balance,
                                                        'today': today})
#######################
# setup_autotopup     #
#######################
@login_required(login_url='/accounts/login/')
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
            card = paylist.data[0].card
            card_type = card.brand
            card_exp_month = card.exp_month
            card_exp_year = card.exp_year
            card_last4 = card.last4
            warn = f"This will override your {card_type} card ending in {card_last4} with expiry {card_exp_month}/{card_exp_year}"

    else:
        stripe.api_key = STRIPE_SECRET_KEY
        customer = stripe.Customer.create()
        auto=AutoTopUpConfig()
        auto.member = request.user
        auto.stripe_customer_id = customer.id
        auto.save()

    return render(request, 'payments/autotopup.html', {'warn': warn})


#######################
# member_transfer     #
#######################
@login_required(login_url='/accounts/login/')
def member_transfer(request):
    """ view to transfer $ to another member
    """

    msg=""

    if request.method == 'POST':
        form = MemberTransfer(request.POST)
        if form.is_valid():
            # Money in
            update_account(member = form.cleaned_data['transfer_to'],
                           other_member = request.user,
                           amount = form.cleaned_data['amount'],
                           description = form.cleaned_data['description'],
                           log_msg = "Member Payment Received %s(%s) to %s(%s) $%s" %
                               (request.user.full_name, request.user.system_number,
                                form.cleaned_data['transfer_to'].full_name,
                                form.cleaned_data['transfer_to'].system_number,
                                form.cleaned_data['amount']),
                           source = "Payments",
                           sub_source = "member_transfer",
                           type = "Transfer In"
                           )
            # Money out
            update_account(member = request.user,
                           other_member = form.cleaned_data['transfer_to'],
                           amount = -form.cleaned_data['amount'],
                           description = form.cleaned_data['description'],
                           log_msg = "Member Payment Sent %s(%s) to %s(%s) $%s" %
                               (request.user.full_name, request.user.system_number,
                                form.cleaned_data['transfer_to'].full_name,
                                form.cleaned_data['transfer_to'].system_number,
                                form.cleaned_data['amount']),
                           source = "Payments",
                           sub_source = "member_transfer",
                           type="Transfer Out"
                           )

            msg = "$%s to %s(%s)" % (form.cleaned_data['amount'],
                                     form.cleaned_data['transfer_to'].full_name,
                                     form.cleaned_data['transfer_to'].system_number)
            return render(request, 'payments/member_transfer_successful.html', {"msg": msg})
        else:
            print(form.errors)

    else:
        form = MemberTransfer()

    try:
        balance_inst = Balance.objects.filter(member=request.user)[0]
        balance = balance_inst.balance
    except IndexError:
        balance = "Nil"


    return render(request, 'payments/member_transfer.html', {'form': form,
                                                             'balance': balance})
