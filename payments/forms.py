""" Payment forms with validation """

from django import forms
from accounts.models import User
from organisations.models import Organisation
from .models import MemberTransaction, TRANSACTION_TYPE

class TestTransaction(forms.Form):
    """ Temporary - will be removed """

    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)
    organisation = forms.ModelChoiceField(queryset=Organisation.objects.all())
    type = forms.ChoiceField(label="Transaction Type", choices=TRANSACTION_TYPE)
    url = forms.CharField(label='URL', max_length=100, required=False)

class MemberTransfer(forms.Form):
    """ M2M transfer form """
    transfer_to = forms.ModelChoiceField(queryset=User.objects.all())
    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    description = forms.CharField(label='Description', max_length=100)

# We need the logged in user to check the balance, add a parameter
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(MemberTransfer, self).__init__(*args, **kwargs)

    def clean_amount(self):
        """ validation for the amount field """
        amount = self.cleaned_data['amount']
        if amount < 0:
            raise forms.ValidationError("Negative amounts are not allowed")
        print(self.user)
        last_tran = MemberTransaction.objects.filter(member=self.user).last()
        if last_tran:
            if amount > last_tran.balance:
                raise forms.ValidationError("Insufficient funds")
        else:
            raise forms.ValidationError("Insufficient funds")
        return amount
