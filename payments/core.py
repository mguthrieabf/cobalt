# -*- coding: utf-8 -*-
"""Handles all activities associated with payments that do not talk to users.

This module handles all of the functions that do not interact directly with
a user. i.e. they do not generally accept a ``Request`` and return an
``HttpResponse``. Arguably these could have been put directly into models.py
but it seems cleaner to store them here.

See also `Payments Views`_. This handles the user side of the interactions.
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

.. _Payments Views:
   #module-payments.views

.. _Payments Overview:
   ./payments_overview.html

"""
import json
import stripe
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from logs.views import log_event
from accounts.models import User
from cobalt.settings import (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY,
                             AUTO_TOP_UP_LOW_LIMIT, GLOBAL_CURRENCY_SYMBOL)
from .models import (StripeTransaction, MemberTransaction,
                     OrganisationTransaction)


#TODO: Complete doco
#######################
# get_balance_detail  #
#######################
def get_balance_detail(member):
    """ Called by dashboard to show basic information

    Args:
        member: A User object - the member whose balance is required

    Returns:
        dict: Keys - balance and last_top_up

    """

    last_tran = MemberTransaction.objects.filter(member=member).last()
    if last_tran:
        balance = "$%s" % last_tran.balance
        return({'balance' : balance, 'last_top_up': last_tran.created_date})
    else:
        return({'balance' : "$0.00", 'last_top_up': None})

################
# get_balance  #
################
def get_balance(member):
    """ Gets member account balance

    This function returns the current balance of the member's account.

    Args:
        member (User): A User object

    Returns:
        float: The member's current balance

    """

    last_tran = MemberTransaction.objects.filter(member=member).last()
    if last_tran:
        balance = float(last_tran.balance)
    else:
        balance = 0.0

    return balance

################################
# stripe_manual_payment_intent #
################################
@login_required()
def stripe_manual_payment_intent(request):
    """ Called from the checkout webpage.

    When a user is going to pay with a credit card we
    tell Stripe and Stripe gets ready for it. By this point in the process
    we have handed over control to the Stripe code which calls this function
    over Ajax.

    This functions expects a json payload as part of `request`.

    Args:
        request - This needs to contain a Json payload.

    Notes:
        The Json should include:
        data{"id": This is the StripeTransaction in our table that we are handling
        "amount": The amount in the system currency}

    Returns:
        json: {'publishableKey':? 'clientSecret':?}

    Notes:
        publishableKey = our Public Stripe key,
        clientSecret = client secret from Stripe

    """

    if request.method == 'POST':
        data = json.loads(request.body)

# check data - do not trust it
        try:
            payload_cents = int(float(data["amount"]) * 100.0)
            payload_cobalt_pay_id = data["id"]
        except KeyError:
            log_event(request=request,
                      user=request.user.full_name,
                      severity="ERROR",
                      source="Payments",
                      sub_source="stripe_manual_payment_intent",
                      message="Invalid payload: %s" % data)
            return JsonResponse({'error': 'Invalid payload'})

# load our StripeTransaction
        try:
            our_trans = StripeTransaction.objects.get(pk=payload_cobalt_pay_id)
        except ObjectDoesNotExist:
            log_event(request=request,
                      user=request.user.full_name,
                      severity="ERROR",
                      source="Payments",
                      sub_source="stripe_manual_payment_intent",
                      message="StripeTransaction id: %s not found" % payload_cobalt_pay_id)

            return JsonResponse({'error': 'Invalid payload'})

# Check it
        if float(our_trans.amount)*100.0 != payload_cents:
            log_event(request=request,
                      user=request.user.full_name,
                      severity="ERROR",
                      source="Payments",
                      sub_source="stripe_manual_payment_intent",
                      message="StripeTransaction id: %s. Browser sent %s cents." %
                      (payload_cobalt_pay_id, payload_cents))
            return JsonResponse({'error': 'Invalid payload'})

        stripe.api_key = STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=payload_cents,
            currency='aud',
            metadata={'cobalt_pay_id': payload_cobalt_pay_id,
                      'cobalt_tran_type': 'Manual'}
            )
        log_event(request=request,
                  user=request.user.full_name,
                  severity="INFO",
                  source="Payments",
                  sub_source="stripe_manual_payment_intent",
                  message="Created payment intent with Stripe. \
                  Cobalt_pay_id: %s" % payload_cobalt_pay_id)

# Update Status
        our_trans.status = "Intent"
        our_trans.save()

        return JsonResponse({'publishableKey':STRIPE_PUBLISHABLE_KEY,
                             'clientSecret': intent.client_secret})

    return JsonResponse({'error': 'POST required'})

####################################
# stripe_auto_payment_intent       #
####################################
@login_required()
def stripe_auto_payment_intent(request):
    """ Called from the auto top up webpage.

    This is very similar to the one off payment. It lets Stripe
    know to expect a credit card and provides a token to confirm
    which one it is.

    When a user is going to set up a credit card we
    tell Stripe and Stripe gets ready for it. By this point in the process
    we have handed over control to the Stripe code which calls this function
    over Ajax.

    This functions expects a json payload as part of `request`.

    Args:
        request - This needs to contain a Json payload.

    Notes:
        The Json should include:
        data{"stripe_customer_id": This is the Stripe customer_id in our table
        for the customer that we are handling}

    Returns:
        json: {'publishableKey':? 'clientSecret':?}

    Notes:
        publishableKey = our Public Stripe key,
        clientSecret = client secret from Stripe

    """

    if request.method == 'POST':

        stripe.api_key = STRIPE_SECRET_KEY
        intent = stripe.SetupIntent.create(
            customer=request.user.stripe_customer_id,
            metadata={'cobalt_member_id': request.user.id,
                      'cobalt_tran_type': 'Auto'}
            )

        log_event(request=request,
                  user=request.user.full_name,
                  severity="INFO",
                  source="Payments",
                  sub_source="stripe_auto_payment_intent",
                  message="Intent created for: %s" % request.user)

        return JsonResponse({'publishableKey':STRIPE_PUBLISHABLE_KEY,
                             'clientSecret': intent.client_secret})

    return JsonResponse({'error': 'POST required'})

######################
# test_callback      #
######################
def test_callback(status, payload, tran):
    """ Eventually I will be moved to another module. I am only here for testing purposes

    I also shouldn't have the 3rd parameter. I only get status and the payload that I provided
    when I made the call to payments to get money from a member. I am responsible for my own
    actions, but for testing I get the StripeTransaction passed so I can reverse it.

    """
    log_event(user="Callback",
              severity="DEBUG",
              source="Payments",
              sub_source="test_callback",
              message="Received callback from payment: %s %s %s" % (status, payload, tran))

#####################
# payment_api       #
#####################
def payment_api(request, description, amount, member, route_code=None,
                route_payload=None, organisation=None, other_member=None,
                log_msg=None, payment_type=None, url=None):
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

    We accept either organisation as the counterpart for this payment or
    other_member. We must have either an organisation or a member, but
    we can't pay to both.

    args:
        request - standard request object
        description - text description of the payment
        amount - how much
        member - User object related to the payment
        route_code - code to map to a callback
        route_payload - value to retirn on completion
        organisation - linked organisation
        other_member - User object
        log_msg - message for the log
        payment_type - description of payment
        url - next url to go to

    returns:
        request - page for user

    """

    print("inside")
    print("Member - %s" % other_member)
    print("Org - %s" % organisation)

    if other_member and organisation: # one or the other, not both
        log_event(user="Stripe API",
                  severity="CRITICAL",
                  source="Payments",
                  sub_source="payments_api",
                  message="Received both other_member and organisation. Code Error.")
        return HttpResponse(status=500)

    if not other_member and not organisation: # must have one
        log_event(user="Stripe API",
                  severity="CRITICAL",
                  source="Payments",
                  sub_source="payments_api",
                  message="Received neither other_member nor organisation. Code Error.")
        return HttpResponse(status=500)


    balance = float(get_balance(member))
    amount = float(amount)

    if not log_msg:
        log_msg = description

    if not payment_type:
        payment_type = "Miscellaneous"

    if not url:  # where to next
        url = "dashboard"

    if amount <= balance:  # sufficient funds

        update_account(member=member,
                       amount=-amount,
                       organisation=organisation,
                       other_member=other_member,
                       description=description,
                       log_msg=log_msg,
                       source="Payments",
                       sub_source="payments_api",
                       payment_type=payment_type
                       )

# If we got an organisation then make their payment too
        if organisation:
            update_organisation(organisation=organisation,
                                amount=amount,
                                description=description,
                                log_msg=log_msg,
                                source="Payments",
                                sub_source="payments_api",
                                payment_type=payment_type,
                                member=member)

            messages.success(request, f"Payment successful! You paid ${amount:.2f} to {organisation}.",
                             extra_tags='cobalt-message-success')

# If we got an other_member then make their payment too
        if other_member:
            update_account(amount=amount,
                           description=description,
                           log_msg=log_msg,
                           source="Payments",
                           sub_source="payments_api",
                           payment_type=payment_type,
                           other_member=member,
                           member=other_member)

            messages.success(request, f"Payment successful! You paid ${amount:.2f} to {other_member}.",
                             extra_tags='cobalt-message-success')

        callback_router(route_code=route_code, route_payload=route_payload, tran=None)

# check for auto top up required - if user not set for auto topup then ignore

        if member.stripe_auto_confirmed:
            if balance - amount < AUTO_TOP_UP_LOW_LIMIT:
                (return_code, msg) = auto_topup_member(member)
                if return_code: # Success
                    messages.success(request, msg,
                                     extra_tags='cobalt-message-success')
                else: # Failure
                    messages.error(request, msg,
                                   extra_tags='cobalt-message-error')

        return redirect(url)

    else: # insufficient funds
        if member.stripe_auto_confirmed:

# calculate required top up amount
# Generally top by the largest of amount and auto_amount, BUT if the
# balance after that will be low enough to require another top up then
# we top up by increments of the top up amount.
            topup_required = amount # normal top up
            if balance < AUTO_TOP_UP_LOW_LIMIT:
                print("balance < AUTO_TOP_UP_LOW_LIMIT")
                if member.auto_amount >= amount: # use biggest
                    print("member.auto_amount >= amount")
                    print("topup_required = member.auto_amount")
                    topup_required = member.auto_amount
                else:
                    print("topup_required = amount")
                    topup_required = amount
                # check if we will still be under threshold
                if balance + topup_required - amount < AUTO_TOP_UP_LOW_LIMIT:
                    print("balance + topup_required - amount < AUTO_TOP_UP_LOW_LIMIT")
                    print("topup_required = member.auto_amount - balance + amount")
                    topup_required = member.auto_amount - balance + amount

####
#### Change from magic number to multiples of auto top up
####

                    min_required_amt = amount - balance + AUTO_TOP_UP_LOW_LIMIT
                    n = int(min_required_amt / member.auto_amount) + 1
                    topup_required = member.auto_amount * n

                    print("top up required: %s" % topup_required)

            else: # not below auto limit, but insufficient funds - use largest of amt and auto
                print("balance < AUTO_TOP_UP_LOW_LIMIT")
                if member.auto_amount >= amount: # use biggest
                    print("member.auto_amount >= amount")
                    print("topup_required = member.auto_amount")
                    topup_required = member.auto_amount

            (return_code, msg) = auto_topup_member(member, topup_required=topup_required)

            if return_code: # success
                update_account(member=member,
                               amount=-amount,
                               organisation=organisation,
                               description=description,
                               log_msg=log_msg,
                               source="Payments",
                               sub_source="payments_api",
                               payment_type=payment_type
                               )

        # If we got an organisation then make their payment too
                if organisation:
                    update_organisation(organisation=organisation,
                                        amount=amount,
                                        description=description,
                                        log_msg=log_msg,
                                        source="Payments",
                                        sub_source="payments_api",
                                        payment_type=payment_type,
                                        member=member)

                    messages.success(request, f"Payment successful! You paid \
                                     ${amount:.2f} to {organisation}.",
                                     extra_tags='cobalt-message-success')

        # If we got an other_member then make their payment too
                if other_member:
                    update_account(amount=amount,
                                   description=description,
                                   log_msg=log_msg,
                                   source="Payments",
                                   sub_source="payments_api",
                                   payment_type=payment_type,
                                   other_member=member,
                                   member=other_member)

                    messages.success(request, f"Payment successful! You paid ${amount:.2f} to {other_member}.",
                                     extra_tags='cobalt-message-success')

                messages.success(request, msg,
                                 extra_tags='cobalt-message-success')
                callback_router(route_code=route_code, route_payload=route_payload,
                                tran=None)
                return redirect(url)


            else: # auto top up failed
                messages.error(request, msg,
                               extra_tags='cobalt-message-error')
                callback_router(route_code=route_code, route_payload=route_payload,
                                tran=None, status="Failed")
                return redirect(url)

        else: # not set up for auto top up - manual payment

# Create Stripe Transaction
            trans = StripeTransaction()
            trans.description = description
            trans.amount = amount - balance
            trans.member = member
            trans.route_code = route_code
            trans.route_payload = route_payload
            trans.linked_amount = amount
            trans.linked_member = other_member
            trans.linked_organisation = organisation
            trans.linked_transaction_type = payment_type
            trans.save()

            msg = "Payment for: " + description
            if balance > 0.0:
                msg = "Partial payment for: %s. <br>Also using your current balance \
                      of %s%.2f to make total payment of %s%.2f." % (description,
                      GLOBAL_CURRENCY_SYMBOL, balance, GLOBAL_CURRENCY_SYMBOL, amount)
            return render(request, 'payments/checkout.html', {'trans': trans,
                                                              'msg': msg})

#########################
# stripe_webhook_manual #
#########################
def stripe_webhook_manual(event):
    """ Handles manual payment events from Stripe webhook

    Called by stripe_webhook to look after incoming manual payments.

    Args:
        event - the event payload from Stripe

    Returns:
        HTTPResponse code - 200 for success, 400 for error
    """

# get data from payload
    charge = event.data.object

# TODO: catch error if ids not present
    log_event(user="Stripe API",
              severity="INFO",
              source="Payments",
              sub_source="stripe_webhook",
              message="Received charge.succeeded for Manual payment. Our id=%s - \
                       Their id=%s" % (charge.metadata.cobalt_pay_id,
                                       charge.id))

# Update StripeTransaction
    try:
        tran = StripeTransaction.objects.get(pk=charge.metadata.cobalt_pay_id)

        tran.stripe_reference = charge.id
        tran.stripe_method = charge.payment_method
        tran.stripe_currency = charge.currency
        tran.stripe_receipt_url = charge.receipt_url
        tran.stripe_brand = charge.payment_method_details.card.brand
        tran.stripe_country = charge.payment_method_details.card.country
        tran.stripe_exp_month = charge.payment_method_details.card.exp_month
        tran.stripe_exp_year = charge.payment_method_details.card.exp_year
        tran.stripe_last4 = charge.payment_method_details.card.last4
        tran.last_change_date = timezone.now()
        tran.status = "Complete"
        tran.save()

        log_event(user="Stripe API",
                  severity="INFO",
                  source="Payments",
                  sub_source="stripe_webhook",
                  message="Successfully updated stripe transaction table. \
                  Our id=%s - Stripe id=%s" % (charge.metadata.cobalt_pay_id,
                                               charge.id))

    except ObjectDoesNotExist:
        log_event(user="Stripe API",
                  severity="CRITICAL",
                  source="Payments",
                  sub_source="stripe_webhook",
                  message="Unable to load stripe transaction. Check StripeTransaction \
                  table. Our id=%s - Stripe id=%s" % (charge.metadata.cobalt_pay_id,
                                                      charge.id))
  # TODO: change to 400
        return HttpResponse(status=200)

# Set the payment type - this could be for a linked transaction or a manual
# payment.

    print("linked?")
    print(tran.linked_transaction_type)
    if tran.linked_transaction_type: # payment for a linked transaction
        paytype = "CC Payment"
    else:  # manual top up
        paytype = "Manual Top Up"

    update_account(member=tran.member,
                   amount=tran.amount,
                   stripe_transaction=tran,
                   description="Payment from card **** **** ***** %s Exp %s/%s" %
                   (tran.stripe_last4, tran.stripe_exp_month,
                    abs(tran.stripe_exp_year) % 100),
                   log_msg="$%s Payment from Stripe Transaction=%s" %
                   (tran.amount, tran.id),
                   source="Payments",
                   sub_source="stripe_webhook",
                   payment_type=paytype
                   )

# Money in from stripe so we can now process the original transaction, if
# we have one. For manual top ups we don't have another transaction and
# linked_transaction_type will be None

    if tran.linked_transaction_type:
        print("linked?")
        print(tran.linked_organisation)
        print(tran.linked_member)

# We could be linked to a member payment or an organisation payment
        if tran.linked_organisation:

            update_account(member=tran.member,
                           amount=-tran.linked_amount,
                           description=tran.description,
                           source="Payments",
                           sub_source="stripe_webhook",
                           payment_type=tran.linked_transaction_type,
                           log_msg=tran.description,
                           organisation=tran.linked_organisation
                           )

        # make organisation payment too
            update_organisation(organisation=tran.linked_organisation,
                                amount=tran.linked_amount,
                                description=tran.description,
                                source="Payments",
                                sub_source="stripe_webhook",
                                payment_type=tran.linked_transaction_type,
                                log_msg=tran.description,
                                member=tran.member)

        if tran.linked_member:

            update_account(member=tran.member,
                           amount=-tran.linked_amount,
                           description=tran.description,
                           source="Payments",
                           sub_source="stripe_webhook",
                           payment_type=tran.linked_transaction_type,
                           log_msg=tran.description,
                           other_member=tran.linked_member,
                           )

        # make member payment too
            update_account(member=tran.linked_member,
                           other_member=tran.member,
                           amount=tran.linked_amount,
                           description=tran.description,
                           source="Payments",
                           sub_source="stripe_webhook",
                           payment_type=tran.linked_transaction_type,
                           log_msg=tran.description,
                           )

    # make Callback
    callback_router(tran.route_code, tran.route_payload, tran)

# succcess
    return HttpResponse(status=200)

##############################
# stripe_webhook_autosetup   #
##############################
def stripe_webhook_autosetup(event):
    """ Handles auto top up setup events from Stripe webhook

    Called by stripe_webhook to look after successful incoming auto top up set ups.

    Args:
        event - the event payload from Stripe

    Returns:
        HTTPResponse code - 200 for success, 400 for error
    """

# Get customer id
    try:
        stripe_customer = event.data.object.customer
    except AttributeError:
        log_event(user="Stripe API",
                  severity="CRITICAL",
                  source="Payments",
                  sub_source="stripe_webhook",
                  message="Error retrieving Stripe customer id from message")
        return HttpResponse(status=400)

# find member
    member = User.objects.filter(stripe_customer_id=stripe_customer).last()
    if not member:
        log_event(user="Stripe API",
                  severity="CRITICAL",
                  source="Payments",
                  sub_source="stripe_webhook",
                  message=f"Error cannot find member with stripe_customer_id={stripe_customer}")
        return HttpResponse(status=400)

# confirm card set up
    member.stripe_auto_confirmed = True
    member.save()

# check if we should make an auto top up now
    balance = get_balance(member)
    if balance < AUTO_TOP_UP_LOW_LIMIT:
        (return_code, message) = auto_topup_member(member)
        if return_code: # success
            log_event(user="Stripe API",
                      severity="INFO",
                      source="Payments",
                      sub_source="stripe_webhook",
                      message=message)
            return HttpResponse(status=200)
        else: # failure
            log_event(user="Stripe API",
                      severity="ERROR",
                      source="Payments",
                      sub_source="stripe_webhook",
                      message=message)
            return HttpResponse(status=200)
    return HttpResponse(status=200)
####################
# stripe_webhook   #
####################
@require_POST
@csrf_exempt
def stripe_webhook(request):
    """ Callback from Stripe webhook

    In development, Stripe sends us everything. In production we can configure
    the events that we receive. This is the only way for Stripe to communicate
    with us.

    Note:
        Stripe sends us multiple similar things, for example *payment.intent.succeeded*
        will accompany anything that uses a payment intent. Be careful to only
        handle one out of the multiple events.

    For **manual payments** we can receive:

    * payment.intent.created - ignore
    * charge.succeeded - process
    * payment.intent.succeeded - ignore

    For **automatic payment set up**, we get:

    * customer.created - ignore
    * setup_intent.created - ignore
    * payment_method.attached - process
    * setup_intent.succeeded - ignore

    For **automatic payments** we get:

    * payment_intent.succeeded - ignore
    * payment_intent.created - ignore
    * charge_succeeded - ignore (we already know this from the API call)

    **Meta data**

    We use meta data to track what the event related to. This is added by us
    when we call Stripe and returned to us by Stripe in the callback.

    Fields used:

    * **cobalt_tran_type** - either *Manual* or *Auto* for manual and auto top up
      transactions. If this is missing then the transaction is invalid.
    * **cobalt_pay_id** - for manual payments this is the linked transaction in
      MemberTransaction.

    Args:
        Stripe json payload - see Stripe documentation

    Returns:
        HTTPStatus Code

"""
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as error:
        # Invalid payload
        log_event(user="Stripe API",
                  severity="HIGH",
                  source="Payments",
                  sub_source="stripe_webhook",
                  message=f"Invalid Payload in message from Stripe: {error}")

        return HttpResponse(status=400)

    try:
        tran_type = event.data.object.metadata.cobalt_tran_type
    except AttributeError:
        print(event)
        log_event(user="Stripe API",
                  severity="CRITICAL",
                  source="Payments",
                  sub_source="stripe_webhook",
                  message="cobalt_tran_type missing from Stripe webhook")
    # TODO: change to 400
        return HttpResponse(status=200)

# We only process change succeeded for Manual charges - for auto topup
# we get this synchronously through the API call, this is additional info.
# Don't process it twice.

    if event.type == 'charge.succeeded' and tran_type == "Manual":
        print("manula and charge succeeded")
        return stripe_webhook_manual(event)

    elif event.type == 'payment_method.attached':  # auto top up set up successful
        return stripe_webhook_autosetup(event)

    else:
        # Unexpected event type
        log_event(user="Stripe API",
                  severity="HIGH",
                  source="Payments",
                  sub_source="stripe_webhook",
                  message="Unexpected event received from Stripe - " + event.type)

        print("Unexpected event found - " + event.type)
        # TODO - change to 400
        return HttpResponse(status=200)

    return HttpResponse(status=200)

#########################
# callback_router       #
#########################
def callback_router(route_code=None, route_payload=None, tran=None, status="Success"):
    """ Central function to handle callbacks

    Callbacks are an asynchronous way for us to let the calling application
    know if a payment successed or not.

    We could use a routing table for this but there will only ever be a small
    number of callbacks in Cobalt so we are okay to hardcode it.

    We should not get tran provided but do for early testing. This will be
    removed later, but for now allows us to reverse the transaction for testing.

    Args:
        route_code - hard coded value to map to a function call
        route_payload - value to return to function
        tran - for testing only. remove later
        status - Success (default) or Failure. Did the payment work or not.

    Returns:
        Nothing
    """

    if route_code:  # do nothing in no route_code passed

        if route_code == "MAN":
            test_callback(status, route_payload, tran)
            log_event(user="Stripe API",
                      severity="INFO",
                      source="Payments",
                      sub_source="stripe_webhook",
                      message="Callback made to: %s" % route_code)
        else:
            log_event(user="Stripe API",
                      severity="CRITICAL",
                      source="Payments",
                      sub_source="stripe_webhook",
                      message="Unable to make callback. Invalid route_code: %s" % route_code)

######################
# update_account     #
######################
def update_account(member, amount, description, log_msg, source,
                   sub_source, payment_type, stripe_transaction=None,
                   other_member=None, organisation=None):
    """ Function to update a customer account

        args:
            member - owner of the account
            amount - value (plus is a deduction, minus is a credit)
            description - to appear on statement
            log_msg - to appear on logs
            source - for logs
            sub_source - for logs
            payment_type - type of payment
            stripe_transaction - linked Stripe transaction (optional)
            other_member - linked member (optional)
            organisation - linked organisation (optional)

        returns:
            nothing

    """
# Get old balance
    balance = get_balance(member) + float(amount)

# Create new MemberTransaction entry
    act = MemberTransaction()
    act.member = member
    act.amount = amount
    act.stripe_transaction = stripe_transaction
    act.other_member = other_member
    act.organisation = organisation
    act.balance = balance
    act.description = description
    act.type = payment_type

    act.save()

    log_event(user=member.full_name,
              severity="INFO",
              source=source,
              sub_source=sub_source,
              message=log_msg + " Updated MemberTransaction table")
#########################
# update_organisation   #
#########################
def update_organisation(organisation, amount, description, log_msg, source,
                        sub_source, payment_type, other_organisation=None,
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
    act.type = payment_type

    act.save()

    log_event(user=member.full_name,
              severity="INFO",
              source=source,
              sub_source=sub_source,
              message=log_msg + " Updated OrganisationTransaction table")

###########################
# auto_topup_member       #
###########################
def auto_topup_member(member, topup_required=None, payment_type="Auto Top Up"):
    """ process an auto top up for a member.

    Internal function to handle a member needing to process an auto top up.
    This function deals with successful top ups and failed top ups. For
    failed top ups it will notify the user and disable auto topups. It is
    the calling functions problem to handle the consequences of the non-payment.

    Args:
        member - a User object.
        topup_required - the amount of the top up (optional). This is required
        if the payment is larger than the top up amount. e.g. balance is 25,
        top up amount is 50, payment is 300.
        payment_type - defaults to Auto Top Up. We allow this to be overriden
        so that a member manually topping up their account using their registered
        auto top up card get the payment type of Manual Top Up on their statement.

    Returns:
        return_code - True for success, False for failure
        message - explanation

    """

    stripe.api_key = STRIPE_SECRET_KEY

    if not member.stripe_auto_confirmed:
        return(False, "Member not set up for Auto Top Up")

    if not member.stripe_customer_id:
        return(False, "No Stripe customer id found")

    if topup_required:
        amount = topup_required
    else:
        amount = member.auto_amount

# Get payment method id for this customer from Stripe
    try:
        paylist = stripe.PaymentMethod.list(
            customer=member.stripe_customer_id,
            type="card",
        )
        pay_method_id = paylist.data[0].id
    except stripe.error.InvalidRequestError:
        log_event(user=member,
                  severity="WARN",
                  source="Payments",
                  sub_source="auto_topup_member",
                  message="Error from stripe - see logs")

        return(False, "Error retreiving customer details from Stripe")

# try payment
    try:
        stripe_return = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency='aud',
            customer=member.stripe_customer_id,
            payment_method=pay_method_id,
            off_session=True,
            confirm=True,
            metadata={'cobalt_tran_type': 'Auto'}
        )

# It worked so create a stripe record
        payload = stripe_return.charges.data[0]

        stripe_tran = StripeTransaction()
        stripe_tran.description = f"Auto top up for \
                                 {member.full_name} ({member.system_number})"
        stripe_tran.amount = amount
        stripe_tran.member = member
        stripe_tran.route_code = None
        stripe_tran.route_payload = None
        stripe_tran.stripe_reference = payload.id
        stripe_tran.stripe_method = payload.payment_method
        stripe_tran.stripe_currency = payload.currency
        stripe_tran.stripe_receipt_url = payload.receipt_url
        stripe_tran.stripe_brand = payload.payment_method_details.card.brand
        stripe_tran.stripe_country = payload.payment_method_details.card.country
        stripe_tran.stripe_exp_month = payload.payment_method_details.card.exp_month
        stripe_tran.stripe_exp_year = payload.payment_method_details.card.exp_year
        stripe_tran.stripe_last4 = payload.payment_method_details.card.last4
        stripe_tran.last_change_date = timezone.now()
        stripe_tran.status = "Complete"
        stripe_tran.save()

# Update members account
        update_account(member=member,
                       amount=amount,
                       description="Payment from %s card **** **** ***** %s Exp %s/%s" %
                       (payload.payment_method_details.card.brand,
                        payload.payment_method_details.card.last4,
                        payload.payment_method_details.card.exp_month,
                        abs(payload.payment_method_details.card.exp_year) % 100),
                       log_msg="$%s %s" % (amount, payment_type),
                       source="Payments",
                       sub_source="auto_topup_member",
                       payment_type=payment_type,
                       stripe_transaction=stripe_tran
                       )

        return(True, "Top up successful. %s%.2f added to your account \
                     from %s card **** **** ***** %s Exp %s/%s" %
                     (GLOBAL_CURRENCY_SYMBOL, amount,
                     payload.payment_method_details.card.brand,
                     payload.payment_method_details.card.last4,
                     payload.payment_method_details.card.exp_month,
                     abs(payload.payment_method_details.card.exp_year) % 100))

    except stripe.error.CardError as error:
        err = error.error
        # Error code will be authentication_required if authentication is needed
        log_event(user=member.full_name,
                  severity="WARN",
                  source="Payments",
                  sub_source="test_autotopup",
                  message="Error from stripe - see logs")

        print("Code is: %s" % err.code)
        # payment_intent_id = err.payment_intent['id']
        # payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
# TODO: handle auth required from Stripe
        return(False, "FIX LATER - MAYBE AUTH required from Stripe")
