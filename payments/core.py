from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from .models import (StripeTransaction, MemberTransaction, AutoTopUpConfig,
                    OrganisationTransaction)
from organisations.models import Organisation
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from logs.views import log_event
from django.contrib import messages
import stripe
import json
from cobalt.settings import (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY,
                            AUTO_TOP_UP_LOW_LIMIT)

#######################
# get_balance_detail  #
#######################
def get_balance_detail(member):
    """ called by dashboard to show basic information """

    last_tran = MemberTransaction.objects.filter(member=member).last()
    if last_tran:
        balance = "$%s" % last_tran.balance
        last_top_up = "Last transaction %s" % last_tran.created_date.strftime('%d %b %Y at %-I:%M %p')
        return({'balance' : balance, 'last_top_up': last_top_up})
    else:
        return({'balance' : "$0.00", 'last_top_up': "No History"})

################
# get_balance  #
################
def get_balance(member):
    """ get members account balance """

    last_tran = MemberTransaction.objects.filter(member=member).last()
    if last_tran:
        balance = last_tran.balance
    else:
        balance = 0.0

    return balance

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

#    if status=="Success":
        # update_account(member = tran.member,
        #                amount = -tran.amount,
        #                stripe_transaction = None,
        #                organisation = Organisation.objects.filter(name = "North Shore Bridge Club Inc")[0],
        #                description = "Summer Festival of Bridge - Swiss Pairs entry",
        #                log_msg = "$%s payment for SFOB" % tran.amount,
        #                source = "Events",
        #                sub_source = "fictional_event_entry_module",
        #                type = "Congress Entry"
        #                )
        #
        # update_organisation(organisation=Organisation.objects.filter(name = "North Shore Bridge Club Inc")[0],
        #                     amount = tran.amount,
        #                     description = "Summer Festival of Bridge - Swiss Pairs entry",
        #                     log_msg = "$%s payment for SFOB" % tran.amount,
        #                     source = "Events",
        #                     sub_source = "fictional_event_entry_module",
        #                     type = "Congress Entry",
        #                     member=tran.member)

#####################
# payment_api       #
#####################
def payment_api(request, description, amount, member, route_code=None,
               route_payload=None, organisation=None, other_member=None,
               log_msg=None, type=None, url=None):
    """ API for payments from other parts of the application.

    There is a user on the end of this who needs to know what is happening,
    so we return a page that tells them. It could be:

    1) A payment page for one off payments
    2) A failed auto payment message
    3) A success page from auto topup
    4) A success page because they had enough funds in the account

    The route_code provides a callback and the route_payload is the string
    to return. For 3 and 4, the callback will be called before the page is
    returned.

    Payments should be the last step in the process for the calling application
    as there is no way to return control to the application after payments is
    done. Note: This would be possible if required.

    amount is the amount to be deducted from the users account. A positive
    amount is a charge, a negative amount is an incoming payment.

"""
    balance = float(get_balance(member))
    amount = float(amount)
    auto_topup = AutoTopUpConfig.objects.filter(member=member).last()
    print("balance: %s" % balance)

    if not log_msg:
        log_msg = description

    if not type:
        type = "Miscellaneous"

    if not url:  # where to next
        url = "dashboard"

    if amount <= balance:  # sufficient funds

        update_account(member=member,
                       amount=-amount,
                       organisation=organisation,
                       description=description,
                       log_msg=log_msg,
                       source="Payments",
                       sub_source="payments_api",
                       type=type
                       )

# If we got an organisation then make their payment too
        update_organisation(organisation=organisation,
                            amount=amount,
                            description=description,
                            log_msg=log_msg,
                            source="Payments",
                            sub_source="payments_api",
                            type=type,
                            member=member)

        messages.success(request, "Payment successful",
                               extra_tags='cobalt-message-success')

        callback_router(route_code=route_code, route_payload=route_payload, tran=None)
        return redirect(url)

# check for auto top up required - if user not set for auto topup then ignore

        if auto_topup:
            if balance - amount < AUTO_TOP_UP_LOW_LIMIT:
                (rc, msg) = auto_topup_member(member)
                if rc:
                    messages.success(request, msg,
                                    extra_tags='cobalt-message-success')
                else:
                    messages.error(request, msg,
                                    extra_tags='cobalt-message-error')

    else: # insufficient funds
        if auto_topup:

# we put the balance after to AUTO_TOP_UP_LOW_LIMIT + auto_topup.auto_amount
            topup_required = AUTO_TOP_UP_LOW_LIMIT + auto_topup.auto_amount - balance + amount

            (rc, msg) = auto_topup_member(member, topup_required=topup_required)

            if rc:
                update_account(member=member,
                               amount=-amount,
                               organisation=organisation,
                               description=description,
                               log_msg=log_msg,
                               source="Payments",
                               sub_source="payments_api",
                               type=type
                               )

        # If we got an organisation then make their payment too
                update_organisation(organisation=organisation,
                                    amount=amount,
                                    description=description,
                                    log_msg=log_msg,
                                    source="Payments",
                                    sub_source="payments_api",
                                    type=type,
                                    member=member)

                messages.success(request, "Payment successful",
                               extra_tags='cobalt-message-success')
                messages.success(request, "Auto top up successful",
                               extra_tags='cobalt-message-success')
                callback_router(route_code=route_code, route_payload=route_payload, tran=None)
                return redirect(url)


            else: # auto top up failed
                messages.error(request, msg,
                              extra_tags='cobalt-message-error')
                callback_router(route_code=route_code, route_payload=route_payload, tran=None, status="Failed")
                return redirect(url)

        else: # not set up for auto top up - manual payment

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
        callback_router(route_code, route_payload, tran)

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

#########################
# callback_router       #
#########################
def callback_router(route_code=None, route_payload=None, tran=None, status="Success"):
    """ Central function to handle callbacks.
    Callbacks are an asynchronous way for us to let the calling application
    know if a payment successed or not.

    We could use a routing table for this but there will only ever be a small
    number of callbacks in Cobalt so we are okay to hardcode it.

    We should not get tran provided but do for early testing. This will be
    removed later, but for now allows us to reverse the transaction for testing
    """
    if route_code:  # do nothing in no route_code passed

        if route_code == "MAN":
            test_callback(status, route_payload, tran)
            log_event(user = "Stripe API",
                      severity = "INFO",
                      source = "Payments",
                      sub_source = "stripe_webhook",
                      message = "Callback made to: %s" % route_code)
        else:
            log_event(user = "Stripe API",
                      severity = "INFO",
                      source = "Payments",
                      sub_source = "stripe_webhook",
                      message = "Unable to make callback. Invalid route_code: %s" % route_code)


######################
# update_account     #
######################
def update_account(member, amount, description, log_msg, source,
                   sub_source, type, stripe_transaction=None,
                   other_member=None, organisation=None):
    """ method to update a customer account """
# Get old balance
    last_tran = MemberTransaction.objects.filter(member=member).last()
    if last_tran:
        balance = float(last_tran.balance) + amount
    else:
        balance = amount

# Create new MemberTransaction entry
    act = MemberTransaction()
    act.member = member
    act.amount = amount
    act.stripe_transaction = stripe_transaction
    act.other_member = other_member
    act.organisation = organisation
    act.balance = balance
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

    last_tran = OrganisationTransaction.objects.last()
    if last_tran:
        balance = last_tran.balance
    else:
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

###########################
# auto_topup_member       #
###########################
def auto_topup_member(member, topup_required=None):
    """ process an auto top up. Optionally pass parameter with amount required
    """

    stripe.api_key = STRIPE_SECRET_KEY
    autotopup = AutoTopUpConfig.objects.filter(member=member).first()

    if not autotopup:
        return(False, "Member not set up for Auto Top Up")

    if topup_required:
        amount = topup_required
    else:
        amount = autotopup.auto_amount

# Get payment method id for this customer from Stripe
    try:
        paylist = stripe.PaymentMethod.list(
          customer=autotopup.stripe_customer_id,
          type="card",
        )
        pay_method_id = paylist.data[0].id
    except InvalidRequestError:
        log_event(user=member,
                  severity="WARN",
                  source="Payments",
                  sub_source="auto_topup_member",
                  message="Error from stripe - see logs")

        return(False, "Error retreiving customer details from Stripe")

# try payment
    try:
        rc = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency='aud',
                customer=autotopup.stripe_customer_id,
                payment_method=pay_method_id,
                off_session=True,
                confirm=True,
        )

        print(rc)

# It worked so create a stripe record
        payload = rc.charges.data[0]

        pi_reference = payload.id
        pi_method = payload.payment_method
        pi_currency = payload.currency
        pi_receipt_url = payload.receipt_url
        pi_brand = payload.payment_method_details.card.brand
        pi_country = payload.payment_method_details.card.country
        pi_exp_month = payload.payment_method_details.card.exp_month
        pi_exp_year = payload.payment_method_details.card.exp_year
        pi_last4 = payload.payment_method_details.card.last4

        stripe_tran = StripeTransaction()
        stripe_tran.description = f"Auto top up for \
                                 {member.full_name} ({member.system_number})"
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
        update_account(member=member,
                       amount=amount,
                       description="Auto Top Up",
                       log_msg="$%s Auto Top Up" % amount,
                       source="Payments",
                       sub_source="auto_topup_member",
                       type="Auto Top Up",
                       stripe_transaction=stripe_tran
                       )

        return(True, "Auto top up successful")

    except stripe.error.CardError as e:
        err = e.error
        # Error code will be authentication_required if authentication is needed
        log_event(user=member.full_name,
                  severity="WARN",
                  source="Payments",
                  sub_source="test_autotopup",
                  message="Error from stripe - see logs")

        print("Code is: %s" % err.code)
        payment_intent_id = err.payment_intent['id']
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return(False, "FIX LATER - MAYBE AUTH required from Stripe")
