from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from .models import Balance, Transaction, Account, AutoTopUp
from .forms import OneOffPayment, TestTransaction, TestAutoTopUp, MemberTransfer
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from logs.views import log_event
import requests
import stripe
import json
from cobalt.settings import STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, GLOBAL_MPSERVER

####################
# Home             #
####################
@login_required(login_url='/accounts/login/')
def home(request):
    """ Default page """
    return render(request, 'payments/home.html')

####################
# get_balance      #
####################
def get_balance(member):
    """ called by dashboard to show basic information """

    try:
        balance_inst = Balance.objects.filter(member=member)[0]
        balance = balance_inst.balance
        top_date = balance_inst.last_top_up_date.strftime('%d %b %Y at %-I:%M %p')
        last_top_up = "Last transaction %s" % (top_date)
    except:
        balance = "Set up Now!"
        last_top_up = "Never"
    return({'balance' : balance, 'last_top_up': last_top_up})

#########################
# create_payment_intent #
#########################
#@login_required(login_url='/accounts/login/')
def create_payment_intent(request):
    """ Called from the checkout webpage.

When a user is going to pay with a credit card we
tell stripe and stripe gets ready for it.

This functions expects a json payload:

  "id": This is the Transaction in our table that we are handling
  "amount": The amount in dollars
  "description": The description on the transaction
  "route_code":  What to notify about the outcome of this Transaction
  "route_payload": What to pass on when we are done

Payments only knows how to pay things, not why. Some other part of the
system needs to be informed once we are done. The route_code tells us
what to call. There are only ever going to be a small number of things
to call so we hard code them.

This function returns our public key and the client secret that we
get back from Stripe
"""

    if request.method == 'POST':
        data = json.loads(request.body)
        trans_amount = int(float(data["amount"]) * 100.0) # pay in cents
        stripe.api_key = STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
                amount=trans_amount,
                currency='aud',
                metadata={'cobalt_pay_id': data["id"]}
                )
        return JsonResponse({'publishableKey':STRIPE_PUBLISHABLE_KEY, 'clientSecret': intent.client_secret})

####################################
# create_payment_superintent       #
####################################
#@login_required(login_url='/accounts/login/')
def create_payment_superintent(request):
    """ Called from the auto top up webpage.

This is very similar to the one off payment. It lets Stripe
know to expect a credit card and provides a token to confirm
which one it is.
"""
    if request.method == 'POST':
        data = json.loads(request.body)
        stripe.api_key = STRIPE_SECRET_KEY
        customer_id=AutoTopUp.objects.filter(member = request.user)[0].stripe_customer_id
        intent = stripe.SetupIntent.create(
                customer = customer_id,
                metadata = {'cobalt_member_id': request.user.id}
                )
        print(intent)
        return JsonResponse({'publishableKey':STRIPE_PUBLISHABLE_KEY, 'clientSecret': intent.client_secret})


######################
# test_callback      #
######################
def test_callback(status, payload, tran):
    """ Eventually I will be moved to another module. I am only here for testing purposes

    I also shouldn't have the 3rd parameter. I only get status and the payload that I provided
    when I made the call to payments to get money from a member. I am responsible for my own
    actions, but for testing I get the transaction passed so I can reverse it.

    """
    log_event(user = "Callback",
              severity = "DEBUG",
              source = "Payments",
              sub_source = "test_callback",
              message = "Received callback from payment: %s %s" % (status, payload))

    if status=="Success":
        update_account(member=tran.member,
                       amount=-tran.amount,
                       counterparty="SFOB",
                       transaction=tran,
                       description="Summer Festival of Bridge - Swiss Pairs entry",
                       log_msg="$%s payment for SFOB" % tran.amount,
                       source="Events",
                       sub_source="fictional_event_entry_module"
                       )

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
    msg=""
    log_event(request = request,
              user = request.user.full_name,
              severity = "INFO",
              source = "Payments",
              sub_source = "test_autotopup",
              message = "User went to auto payment screen")

    if request.method == 'POST':
        form = TestAutoTopUp(request.POST)
        if form.is_valid():

            description = form.cleaned_data['description']
            amount = form.cleaned_data['amount']
            member = form.cleaned_data['payer']

            autotopup = get_object_or_404(AutoTopUp, member=member)

            stripe.api_key = STRIPE_SECRET_KEY

# Get payment method id for this customer from Stripe
            paylist = stripe.PaymentMethod.list(
              customer=autotopup.stripe_customer_id,
              type="card",
            )
            pay_method_id = paylist.data[0].id

# try payment
            try:
              rc=stripe.PaymentIntent.create(
                amount=amount * 100,
                currency='aud',
                customer=autotopup.stripe_customer_id,
                payment_method=pay_method_id,
                off_session=True,
                confirm=True,
              )
              print(rc)
              update_account(member=member,
                             amount=amount,
                             counterparty="Auto Top Up",
                             description="Auto Top Up",
                             log_msg="$%s Auto Top Up" % amount,
                             source="Payments",
                             sub_source="auto_top_up"
                             )
              msg="Top Up Successful"
            except stripe.error.CardError as e:
              err = e.error
              # Error code will be authentication_required if authentication is needed
              print("Code is: %s" % err.code)
              payment_intent_id = err.payment_intent['id']
              payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

#            return payment_api(request, description, amount, member, route_code, route_payload)
    else:
        form = TestAutoTopUp()

    return render(request, 'payments/test_autotopup.html', {'form': form, 'msg': msg})

##########################
# test_transaction       #
##########################
@login_required(login_url='/accounts/login/')
def test_transaction(request):
    """ Temporary way to make a change to ABF $ account """

    msg=""

    log_event(request = request,
              user = request.user.full_name,
              severity = "INFO",
              source = "Payments",
              sub_source = "test_payment",
              message = "User went to test transaction screen")

    if request.method == 'POST':
        form = TestTransaction(request.POST)
        if form.is_valid():
            update_account(member=form.cleaned_data['payer'],
                           amount=-form.cleaned_data['amount'],
                           counterparty=form.cleaned_data['counterparty'],
                           description=form.cleaned_data['description'],
                           log_msg="Manual Payments Update: $%s %s" %
                               (form.cleaned_data['amount'], form.cleaned_data['description']),
                           source="Payments",
                           sub_source="test_transaction"
                           )
            msg = "Update applied"

    else:
        form = TestTransaction()

    return render(request, 'payments/test_transaction.html', {'form': form, 'msg': msg})

#####################
# payment_api       #
#####################
def payment_api(request, description, amount, member, route_code=None, route_payload=None):
    """ API for one off payments from other parts of the application

The route_code provides a callback and the route_payload is the string
to return.

"""
    trans = Transaction()
    trans.description = description
    trans.amount = amount
    trans.member = member
    trans.route_code = route_code
    trans.route_payload = route_payload
    trans.save()
    return render(request, 'payments/checkout.html', {'trans': trans})

####################
# stripe_webhook   #
####################
@require_POST
@csrf_exempt
def stripe_webhook(request):
    """ Callback from Stipe webhook """
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
          json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        log_event(user = "Stripe API",
              severity = "HIGH",
              source = "Payments",
              sub_source = "stripe_webhook",
              message = "Invalid Payload in message from Stripe")

        print("Invalid payload")
        return HttpResponse(status=400)

    if event.type == 'payment_intent.succeeded':
    # get data from payload
        payment_intent  = event.data.object

        pi_reference    = payment_intent.id
        pi_method       = payment_intent.payment_method
        pi_amount       = payment_intent.amount
        pi_currency     = payment_intent.currency
        pi_payment_id   = payment_intent.metadata.cobalt_pay_id
        pi_receipt_url  = payment_intent.charges.data[0].receipt_url
        pi_brand        = payment_intent.charges.data[0].payment_method_details.card.brand
        pi_country      = payment_intent.charges.data[0].payment_method_details.card.country
        pi_exp_month    = payment_intent.charges.data[0].payment_method_details.card.exp_month
        pi_exp_year     = payment_intent.charges.data[0].payment_method_details.card.exp_year
        pi_last4        = payment_intent.charges.data[0].payment_method_details.card.last4

        log_event(user = "Stripe API",
                  severity = "INFO",
                  source = "Payments",
                  sub_source = "stripe_webhook",
                  message = "Received payment_intent.succeeded. Our id=%s - Their id=%s" % (pi_payment_id, pi_reference))
    # Update transaction

        try:
            tran = Transaction.objects.get(pk=pi_payment_id)

            tran.stripe_reference = pi_reference
            tran.stripe_method = pi_method
            tran.stripe_currency = pi_currency
            tran.stripe_receipt_url = pi_receipt_url
            tran.stripe_brand = pi_brand
            tran.stripe_country = pi_country
            tran.stripe_exp_month = pi_exp_month
            tran.stripe_exp_year = pi_exp_year
            tran.stripe_last4 = pi_last4
            tran.last_change_date = timezone.now()
            tran.status = "Complete"
            tran.save()

            log_event(user = "Stripe API",
                      severity = "INFO",
                      source = "Payments",
                      sub_source = "stripe_webhook",
                      message = "Successfully updated transaction table. Our id=%s - Stripe id=%s" % (pi_payment_id, pi_reference))

        except ObjectDoesNotExist:
            log_event(user = "Stripe API",
                      severity = "CRITICAL",
                      source = "Payments",
                      sub_source = "stripe_webhook",
                      message = "Unable to load transaction. Check Transaction table. Our id=%s - Stripe id=%s" % (pi_payment_id, pi_reference))

        update_account(member=tran.member,
                       amount=tran.amount,
                       counterparty="CC Payment",
                       transaction=tran,
                       description="Payment from card **** **** ***** %s Exp %s/%s" %
                           (tran.stripe_last4, tran.stripe_exp_month, abs(tran.stripe_exp_year) % 100),
                       log_msg="$%s Payment from Stripe Transaction=%s" % (tran.amount, tran.id),
                       source="Payments",
                       sub_source="stripe_webhook"
                       )

        # make Callback
        if tran.route_code == "MAN":
            test_callback("Success", tran.route_payload, tran)
            log_event(user = "Stripe API",
                      severity = "INFO",
                      source = "Payments",
                      sub_source = "stripe_webhook",
                      message = "Callback made to: %s" % tran.route_code)
        else:
            log_event(user = "Stripe API",
                      severity = "INFO",
                      source = "Payments",
                      sub_source = "stripe_webhook",
                      message = "Unable to make callback. Invalid route_code: %s" % tran.route_code)

    else:
        # Unexpected event type
        log_event(user = "Stripe API",
                  severity = "HIGH",
                  source = "Payments",
                  sub_source = "stripe_webhook",
                  message = "Unexpected event received from Stripe - " + event.type)

        print("Unexpected event found - " + event.type)
        return HttpResponse(status=400)

    return HttpResponse(status=200)

######################
# update_account     #
######################
def update_account(member, amount, counterparty, description, log_msg, source, sub_source, transaction=None):
    """ method to update a customer account """
    try:
        balance = Balance.objects.filter(member = member)[0]
    except:
        balance = Balance()
        balance.balance=0
        balance.member = member
    balance.balance += amount
    balance.last_top_up_amount = amount
    balance.save()

    log_event(user = member.full_name,
              severity = "INFO",
              source = source,
              sub_source = sub_source,
              message = log_msg + " Updated balance table")

# Create new account entry
    act = Account()
    act.member = member
    act.amount = amount
    act.counterparty = counterparty
    act.transaction = transaction
    act.balance = balance.balance
    act.description = description

    act.save()

    log_event(user = member.full_name,
              severity = "INFO",
              source = source,
              sub_source = sub_source,
              message = log_msg + " Updated account table")

#####################
# statement         #
#####################
@login_required(login_url='/accounts/login/')
def statement(request):
    """ Member statement view
    """

# Get summary data
    qry = '%s/mps/%s' % (GLOBAL_MPSERVER, request.user.abf_number)
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

    events_list = Account.objects.filter(member=request.user).order_by('-created_date')
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
                                                        'balance': balance})

#######################
# setup_autotopup     #
#######################
@login_required(login_url='/accounts/login/')
def setup_autotopup(request):
    """ view to sign up to auto top up
    """

# Already a customer?
    autotopup = AutoTopUp.objects.filter(member=request.user)
    if autotopup:                           # record exists
        print("auto top up record found")
        if autotopup[0].stripe_customer_id:    # cust_id exists
            print("Found autotopup with stripe details")

            # need to fix logic - if autotopup & a.stripe_c_id
    else:
        stripe.api_key = STRIPE_SECRET_KEY
        customer = stripe.Customer.create()
        auto=AutoTopUp()
        auto.member = request.user
        auto.stripe_customer_id = customer.id
        auto.save()

    return render(request, 'payments/autotopup.html', {})


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
            update_account(member=form.cleaned_data['transfer_to'],
                           amount=form.cleaned_data['amount'],
                           counterparty="Transfer from: %s (%s)" % (request.user.full_name, request.user.abf_number),
                           description=form.cleaned_data['description'],
                           log_msg="Member Payment Received %s(%s) to %s(%s) $%s" %
                               (request.user.full_name, request.user.abf_number,
                                form.cleaned_data['transfer_to'].full_name,
                                form.cleaned_data['transfer_to'].abf_number,
                                form.cleaned_data['amount']),
                           source="Payments",
                           sub_source="member_transfer"
                           )
            # Money out
            update_account(member=request.user,
                           amount=-form.cleaned_data['amount'],
                           counterparty="Transfer to: %s (%s)" % (form.cleaned_data['transfer_to'].full_name, form.cleaned_data['transfer_to'].abf_number),
                           description=form.cleaned_data['description'],
                           log_msg="Member Payment Sent %s(%s) to %s(%s) $%s" %
                               (request.user.full_name, request.user.abf_number,
                                form.cleaned_data['transfer_to'].full_name,
                                form.cleaned_data['transfer_to'].abf_number,
                                form.cleaned_data['amount']),
                           source="Payments",
                           sub_source="member_transfer"
                           )

            msg = "$%s to %s(%s)" % (form.cleaned_data['amount'],
                                     form.cleaned_data['transfer_to'].full_name,
                                     form.cleaned_data['transfer_to'].abf_number)
            return render(request, 'payments/member-transfer-successful.html', {"msg": msg})
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
