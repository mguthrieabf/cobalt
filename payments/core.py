from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from .models import Balance, StripeTransaction, MemberTransaction, AutoTopUpConfig, OrganisationTransaction
from organisations.models import Organisation
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from logs.views import log_event
import stripe
import json
from cobalt.settings import STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY

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
@login_required()
def create_payment_intent(request):
    """ Called from the checkout webpage.

When a user is going to pay with a credit card we
tell stripe and stripe gets ready for it.

This functions expects a json payload:

  "id": This is the StripeTransaction in our table that we are handling
  "amount": The amount in dollars

Payments only knows how to pay things, not why. Some other part of the
system needs to be informed once we are done. The route_code tells us
what to call. There are only ever going to be a small number of things
to call so we hard code them.

This function returns our public key and the client secret that we
get back from Stripe
"""

    if request.method == 'POST':
        data = json.loads(request.body)

# check data - do not trust it
        try:
            payload_cents = int(float(data["amount"]) * 100.0)
            payload_cobalt_pay_id = data["id"]
        except:
            log_event(request = request,
                  user = request.user.full_name,
                  severity = "ERROR",
                  source = "Payments",
                  sub_source = "create_payment_intent",
                  message = "Invalid payload: %s" % data)
            return JsonResponse({'error': 'Invalid payload'})

# load our StripeTransaction
        try:
            our_trans = StripeTransaction.objects.get(pk=payload_cobalt_pay_id)
        except ObjectDoesNotExist:
            log_event(request = request,
                  user = request.user.full_name,
                  severity = "ERROR",
                  source = "Payments",
                  sub_source = "create_payment_intent",
                  message = "StripeTransaction id: %s not found" % payload_cobalt_pay_id)
            return JsonResponse({'error': 'Invalid payload'})

# Check it
        if float(our_trans.amount)*100.0 != payload_cents:
            log_event(request = request,
                  user = request.user.full_name,
                  severity = "ERROR",
                  source = "Payments",
                  sub_source = "create_payment_intent",
                  message = "StripeTransaction id: %s. Browser sent %s cents." %
                        (payload_cobalt_pay_id, payload_cents))
            return JsonResponse({'error': 'Invalid payload'})

        stripe.api_key = STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
                amount = payload_cents,
                currency = 'aud',
                metadata = {'cobalt_pay_id': payload_cobalt_pay_id}
                )
        log_event(request = request,
                  user = request.user.full_name,
                  severity = "INFO",
                  source = "Payments",
                  sub_source = "create_payment_intent",
                  message = "Created payment intent with Stripe. Cobalt_pay_id: %s" % payload_cobalt_pay_id)

# Update Status
        our_trans.status = "Intent"
        our_trans.save()

        return JsonResponse({'publishableKey':STRIPE_PUBLISHABLE_KEY, 'clientSecret': intent.client_secret})

####################################
# create_payment_superintent       #
####################################
@login_required()
def create_payment_superintent(request):
    """ Called from the auto top up webpage.

This is very similar to the one off payment. It lets Stripe
know to expect a credit card and provides a token to confirm
which one it is.
"""
    if request.method == 'POST':
        data = json.loads(request.body)

        try:
            auto_top = AutoTopUpConfig.objects.get(member=request.user)
        except ObjectDoesNotExist:
            log_event(request = request,
                  user = request.user.full_name,
                  severity = "ERROR",
                  source = "Payments",
                  sub_source = "create_payment_superintent",
                  message = "No AutoTopUpConfig for user: %s" % request.user)
            return JsonResponse({'error': 'user not found'})

        stripe.api_key = STRIPE_SECRET_KEY
        intent = stripe.SetupIntent.create(
                customer = auto_top.stripe_customer_id,
                metadata = {'cobalt_member_id': request.user.id}
                )

        log_event(request = request,
              user = request.user.full_name,
              severity = "INFO",
              source = "Payments",
              sub_source = "create_payment_superintent",
              message = "Intent created for: %s" % request.user)

        return JsonResponse({'publishableKey':STRIPE_PUBLISHABLE_KEY, 'clientSecret': intent.client_secret})


######################
# test_callback      #
######################
def test_callback(status, payload, tran):
    """ Eventually I will be moved to another module. I am only here for testing purposes

    I also shouldn't have the 3rd parameter. I only get status and the payload that I provided
    when I made the call to payments to get money from a member. I am responsible for my own
    actions, but for testing I get the StripeTransaction passed so I can reverse it.

    """
    log_event(user = "Callback",
              severity = "DEBUG",
              source = "Payments",
              sub_source = "test_callback",
              message = "Received callback from payment: %s %s" % (status, payload))

    if status=="Success":
        update_account(member = tran.member,
                       amount = -tran.amount,
                       stripe_transaction = None,
                       organisation = Organisation.objects.filter(name = "North Shore Bridge Club Inc")[0],
                       description = "Summer Festival of Bridge - Swiss Pairs entry",
                       log_msg = "$%s payment for SFOB" % tran.amount,
                       source = "Events",
                       sub_source = "fictional_event_entry_module",
                       type = "Congress Entry"
                       )

        update_organisation(organisation=Organisation.objects.filter(name = "North Shore Bridge Club Inc")[0],
                            amount = tran.amount,
                            description = "Summer Festival of Bridge - Swiss Pairs entry",
                            log_msg = "$%s payment for SFOB" % tran.amount,
                            source = "Events",
                            sub_source = "fictional_event_entry_module",
                            type = "Congress Entry",
                            member=tran.member)

#####################
# payment_api       #
#####################
def payment_api(request, description, amount, member, route_code=None, route_payload=None):
    """ API for payments from other parts of the application

The route_code provides a callback and the route_payload is the string
to return.

"""
    trans = StripeTransaction()
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
    """ Callback from Stripe webhook """
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
    # Update StripeTransaction

        try:
            tran = StripeTransaction.objects.get(pk=pi_payment_id)

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
                      message = "Successfully updated stripe transaction table. Our id=%s - Stripe id=%s" % (pi_payment_id, pi_reference))

        except ObjectDoesNotExist:
            log_event(user = "Stripe API",
                      severity = "CRITICAL",
                      source = "Payments",
                      sub_source = "stripe_webhook",
                      message = "Unable to load stripe transaction. Check StripeTransaction table. Our id=%s - Stripe id=%s" % (pi_payment_id, pi_reference))

        update_account(member = tran.member,
                       amount = tran.amount,
                       stripe_transaction = tran,
                       description = "Payment from card **** **** ***** %s Exp %s/%s" %
                           (tran.stripe_last4, tran.stripe_exp_month, abs(tran.stripe_exp_year) % 100),
                       log_msg = "$%s Payment from Stripe Transaction=%s" % (tran.amount, tran.id),
                       source = "Payments",
                       sub_source = "stripe_webhook",
                       type = "CC Payment"
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
def update_account(member, amount, description, log_msg, source,
                   sub_source, type, stripe_transaction=None,
                   other_member=None, organisation=None):
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

# Create new MemberTransaction entry
    act = MemberTransaction()
    act.member = member
    act.amount = amount
    act.stripe_transaction = stripe_transaction
    act.other_member = other_member
    act.organisation = organisation
    act.balance = balance.balance
    act.description = description
    act.type = type

    act.save()

    log_event(user = member.full_name,
              severity = "INFO",
              source = source,
              sub_source = sub_source,
              message = log_msg + " Updated MemberTransaction table")
#########################
# update_organisation   #
#########################
def update_organisation(organisation, amount, description, log_msg, source,
                   sub_source, type, other_organisation=None,
                   member=None):
    """ method to update an organisations account """

    try:
        balance = OrganisationTransaction.objects.last().balance
    except AttributeError:
        balance = 0.0

    act = OrganisationTransaction()
    act.organisation = organisation
    act.member = member
    act.amount = amount
    act.other_organisation = other_organisation
    act.balance = balance
    act.description = description
    act.type = type

    act.save()

    log_event(user = member.full_name,
              severity = "INFO",
              source = source,
              sub_source = sub_source,
              message = log_msg + " Updated OrganisationTransaction table")
