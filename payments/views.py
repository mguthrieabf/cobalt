from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from .models import Balance, Transaction, Account
from .forms import OneOffPayment, Checkout
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from logs.views import log_event
import stripe
import json
from cobalt.settings import STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY

@login_required(login_url='/accounts/login/')
def home(request):
    """ Default page """
    return render(request, 'payments/home.html')

# @login_required(login_url='/accounts/login/')
def get_balance(system_number):
    """ called by dashboard to show basic information """

    try:
        member = Balance.objects.filter(system_number = system_number)
        balance = member[0].balance
        top_date = member[0].last_top_up_date.strftime('%d %b %Y at %-I:%M %p')
        last_top_up = "Last top up %s ($%s)" % (top_date,
                                               member[0].last_top_up_amount)
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

def test_callback(status, payload):
    log_event("Callback" , "DEBUG",
                  "Payments", "test_callback", "Received callback from payment: %s %s" % (status, payload) )

@login_required(login_url='/accounts/login/')
def test_payment(request):
###################################################
# view for simple payments                        #
###################################################
    log_event("%s %s" % (request.user.first_name, request.user.last_name), "INFO",
              "Payments", "test_payment", "User went to test payment screen")

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
############################################
# callback from Stripe                     #
############################################
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
          json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        log_event("Stripe API", "HIGH", "Payments", "stripe_webhook", "Invalid Payload in message from Stripe")

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

        log_event("Stripe API", "INFO", "Payments", "stripe_webhook", "Received payment_intent.succeeded. Our id=%s - Their id=%s" % (pi_payment_id, pi_reference))

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

            log_event("Stripe API", "INFO", "Payments", "stripe_webhook",
                "Successfully updated transaction table. Our id=%s - Stripe id=%s" % (pi_payment_id, pi_reference))

            # make Callback

            if tran.route_code == "MAN":
                test_callback("Success", tran.route_payload)
            else:
                log_event("Stripe API", "CRITICAL", "Payments", "stripe_webhook",
                    "Unable to make callback. Invalid route_code: %s" % tran.route_code)


        except ObjectDoesNotExist:
            print("NOT FOUND!!!!")
            log_event("Stripe API", "CRITICAL", "Payments", "stripe_webhook",
                "Unable to load transaction. Check Transaction table. Our id=%s - Stripe id=%s" % (pi_payment_id, pi_reference))

        try:
            balance = Balance.objects.filter(system_number = tran.member.abf_number)[0]
        except:
            balance = Balance()
            balance.balance=0
            
        balance.balance += tran.amount
        balance.save()

        log_event("%s %s" % (tran.member.first_name, tran.member.last_name), "INFO", "Payments", "stripe_webhook",
            "Successfully updated balance table after Stripe payment of $%s" % (tran.amount))

        act = Account()
        act.member = tran.member
        act.amount = tran.amount
        act.counterparty = "Stripe"
        act.transaction = tran
        act.balance = balance.balance
        act.description = "Payment from card ending in %s Exp %s/%s" % (tran.stripe_last4, tran.stripe_exp_month, abs(tran.stripe_exp_year) % 100)

        act.save()

        log_event("%s %s" % (act.member.first_name, act.member.last_name), "INFO", "Payments", "stripe_webhook",
            "Successfully updated account table after Stripe payment of $%s" % (act.amount))



    elif event.type == 'payment_method.attached':
        payment_method = event.data.object # contains a stripe.PaymentMethod
        # Then define and call a method to handle the successful attachment of a PaymentMethod.
        # handle_payment_method_attached(payment_method)
      # ... handle other event types
        print(payment_method)
    else:
        # Unexpected event type
        log_event("Stripe API", "HIGH", "Payments", "stripe_webhook", "Unexpected event received from Stripe - " + event.type)
        print("Unexpected event found - " + event.type)
        return HttpResponse(status=400)

    return HttpResponse(status=200)


def statement(request):
    events_list = Account.objects.filter(member=request.user).order_by('-created_date')
    page = request.GET.get('page', 1)

    paginator = Paginator(events_list, 10)
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)

    return render(request, 'payments/statement.html', { 'events': events })
