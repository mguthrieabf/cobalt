from django import forms
from accounts.models import User
from organisations.models import Organisation
from .models import MemberTransaction

class OneOffPayment(forms.Form):
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)
    route_code = forms.CharField(label="Internal routing code for callback", max_length=4)
    route_payload = forms.CharField(label="Payload to return to callback", max_length=40)

class AutoTopUpConfig(forms.Form):
    auto_amount = forms.IntegerField(label='Auto Top Up Amount')

class TestTransaction(forms.Form):
    payer = forms.ModelChoiceField(queryset=User.objects.all())
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)
    counterparty = forms.ModelChoiceField(queryset=Organisation.objects.all())

class TestAutoTopUp(forms.Form):
    payer = forms.ModelChoiceField(queryset=User.objects.all())
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)

class MemberTransfer(forms.Form):
    transfer_to = forms.ModelChoiceField(queryset=User.objects.all())
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', required=False, max_length=100)

# We need the logged in user to check the balance, add a parameter
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(MemberTransfer, self).__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 0:
            raise forms.ValidationError("Negative amounts are not allowed")
        print(self.user)
        last_tran = MemberTransaction.objects.filter(member=self.user).last()
        if last_tran:
            if amount > last_tran.balance:
                raise(forms.ValidationError("Insufficient funds"))
        else:
                raise(forms.ValidationError("Insufficient funds"))
        return amount
