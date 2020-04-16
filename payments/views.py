from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from .models import Balance, Transaction, Account
from .forms import OneOffPayment, TestTransaction
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from logs.views import log_event
import requests
import stripe
import json
from cobalt.settings import STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, GLOBAL_MPSERVER

@login_required(login_url='/accounts/login/')
def home(request):
    """ Default page """
    return render(request, 'payments/home.html')

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
        details = {
            'member': tran.member,
            'amount': -tran.amount,
            'counterparty': "SFOB",
            'transaction': tran,
            'description': "Summer Festival Of Bridge - Swiss Pairs entry",
            'log_msg': "$%s payment for SFOB" % tran.amount,
            'source': "Events",
            'sub_source': "fictional_event_entry_module"
        }

        update_account(details)

@login_required(login_url='/accounts/login/')
def test_payment(request):
###################################################
# view for simple payments                        #
###################################################
    log_event(request = request,
              user = request.user.full_name,
              severity = "INFO",
              source = "Payments",
              sub_source = "test_payment",
              message = "User went to test payment screen")

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
            details = {
                'member': form.cleaned_data['payer'],
                'amount': form.cleaned_data['amount'],
                'counterparty': form.cleaned_data['counterparty'],
                'transaction': None,
                'description': form.cleaned_data['description'],
                'log_msg': "Manual Payments Update: $%s %s" %
                    (form.cleaned_data['amount'], form.cleaned_data['description']),
                'source': "Payments",
                'sub_source': "test_transaction"
            }
            update_account(details)
            msg = "Update applied"

    else:
        form = TestTransaction()

    return render(request, 'payments/test_transaction.html', {'form': form, 'msg': msg})

def payment_api(request, description, amount, member, route_code, route_payload):
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

        details = {
            'member': tran.member,
            'amount': tran.amount,
            'counterparty': "CC Payment",
            'transaction': tran,
            'description': "Payment from card **** **** ***** %s Exp %s/%s" %
                (tran.stripe_last4, tran.stripe_exp_month, abs(tran.stripe_exp_year) % 100),
            'log_msg': "$%s Payment from Stripe Transaction=%s" % (tran.amount, tran.id),
            'source': "Payments",
            'sub_source': "stripe_webhook"
        }

        update_account(details)

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

def update_account(details):
    """ method to update a customer account """
    try:
        balance = Balance.objects.filter(member = details['member'])[0]
    except:
        balance = Balance()
        balance.balance=0
        balance.member = details['member']
    balance.balance += details['amount']
    balance.last_top_up_amount = details['amount']
    balance.save()

    log_event(user = details['member'].full_name,
              severity = "INFO",
              source = details['source'],
              sub_source = details['sub_source'],
              message = details['log_msg'] + " Updated balance table")


# Create new account entry
    act = Account()
    act.member = details['member']
    act.amount = details['amount']
    act.counterparty = details['counterparty']
    act.transaction = details['transaction']
    act.balance = balance.balance
    act.description = details['description']

    act.save()

    log_event(user = details['member'].full_name,
              severity = "INFO",
              source = details['source'],
              sub_source = details['sub_source'],
              message = details['log_msg'] + " Updated account table")


@login_required(login_url='/accounts/login/')
def statement(request):

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

    events_list = Account.objects.filter(member=request.user).order_by('-created_date')
    page = request.GET.get('page', 1)

    paginator = Paginator(events_list, 30)
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)

    return render(request, 'payments/statement.html', { 'events': events, "user": request.user, "summary": summary, "club": club})
