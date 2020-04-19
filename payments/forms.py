from django import forms
from accounts.models import User

class OneOffPayment(forms.Form):
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)
    route_code = forms.CharField(label="Internal routing code for callback", max_length=4)
    route_payload = forms.CharField(label="Payload to return to callback", max_length=40)

class AutoTopUp(forms.Form):
    auto_amount = forms.IntegerField(label='Auto Top Up Amount')

class TestTransaction(forms.Form):
    payer = forms.ModelChoiceField(queryset=User.objects.all())
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)
    counterparty = forms.CharField(label='Counterparty', max_length=80)

class TestAutoTopUp(forms.Form):
    payer = forms.ModelChoiceField(queryset=User.objects.all())
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)
