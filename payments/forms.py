from django import forms

class OneOffPayment(forms.Form):
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)
    route_code = forms.CharField(label="Internal routing code for callback", max_length=4)
    route_payload = forms.CharField(label="Payload to return to callback", max_length=40)

class Checkout(forms.Form):
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    currency = forms.CharField(label='Currency', max_length=3)
