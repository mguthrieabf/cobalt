from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
from .models import Balance, Transaction
from .forms import OneOffPayment, Checkout
from django.http import HttpResponseRedirect
from django.http import JsonResponse
import stripe
import json
from cobalt.settings import STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY

@login_required(login_url='/accounts/login/')
def home(request):
    return render(request, 'payments/home.html')

# @login_required(login_url='/accounts/login/')
def get_balance(system_number):
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
# When a user is going to pay with a credit card we tell stripe and stripe gets ready for it
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data["amount"])
        trans_amount = int(float(data["amount"]) * 100.0)
        stripe.api_key = STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
                amount=trans_amount,
                currency='aud',
                metadata={'cobalt_pay_id': data["id"]}
                )
        return JsonResponse({'publishableKey':STRIPE_PUBLISHABLE_KEY, 'clientSecret': intent.client_secret})

@login_required(login_url='/accounts/login/')
def test_payment(request):
    if request.method == 'POST':
        form = OneOffPayment(request.POST)
        if form.is_valid():
            trans = Transaction()
            trans.description = form.cleaned_data['description']
            trans.amount = form.cleaned_data['amount']
            trans.member = request.user
            trans.save()
            return render(request, 'payments/checkout.html', {'trans': trans})
    else:
        form = OneOffPayment()

    return render(request, 'payments/test_payment.html', {'form': form})




#@require_http_methods(["GET", "POST"])
@require_POST
@csrf_exempt
def stripe_webhook(request):
  payload = request.body
  event = None

  try:
    event = stripe.Event.construct_from(
      json.loads(payload), stripe.api_key
    )
  except ValueError as e:
    # Invalid payload
    print("Invalid payload")
    return HttpResponse(status=400)

  # Handle the event
  if event.type == 'payment_intent.succeeded':
    payment_intent = event.data.object # contains a stripe.PaymentIntent
    # Then define and call a method to handle the successful payment intent.
    # handle_payment_intent_succeeded(payment_intent)
    print(payment_intent)
  elif event.type == 'payment_method.attached':
    payment_method = event.data.object # contains a stripe.PaymentMethod
    # Then define and call a method to handle the successful attachment of a PaymentMethod.
    # handle_payment_method_attached(payment_method)
  # ... handle other event types
    print(payment_method)
  else:
    # Unexpected event type
    print("Unexpected event")
    return HttpResponse(status=400)

  return HttpResponse(status=200)

#@login_required(login_url='/accounts/login/')
def checkout(request):
    return render(request, 'payments/checkout.html')

# @login_required(login_url='/accounts/login/')
# def test_oneoff_payment(request):
#
#     if request.method == 'POST':
#         form = OneOffPayment(request.POST)
#         if form.is_valid():
#             checkout=Checkout()
#             checkout.amount = form.cleaned_data.get("amount")
#             return render(request, 'payments/checkout.html', {'form': checkout})
#     else:
#         form = OneOffPayment()
#
#     return render(request, 'payments/oneoffpayment.html', {'form': form})
