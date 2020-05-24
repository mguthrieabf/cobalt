""" Payment forms with validation """

from django import forms
from accounts.models import User
from organisations.models import Organisation
from cobalt.settings import (AUTO_TOP_UP_MIN_AMT, AUTO_TOP_UP_MAX_AMT,
                             GLOBAL_CURRENCY_SYMBOL)
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

    # def clean_amount(self):
    #     """ validation for the amount field """
    #     amount = self.cleaned_data['amount']
    #     if amount < 0:
    #         raise forms.ValidationError("Negative amounts are not allowed")
    #     print(self.user)
    #     last_tran = MemberTransaction.objects.filter(member=self.user).last()
    #     if last_tran:
    #         if amount > last_tran.balance:
    #             raise forms.ValidationError("Insufficient funds")
    #     else:
    #         raise forms.ValidationError("Insufficient funds")
    #     return amount

class ManualTopup(forms.Form):
    """ Manual top up form """

    CARD_CHOICES = [("Existing", "Use Registered Card"),
                    ("Another", "Use Another Card")]

    amount = forms.DecimalField(label='Amount', max_digits=8, decimal_places=2)
    card_choice = forms.ChoiceField(label="Card Option", choices=CARD_CHOICES,
                                    required=False)

    def clean(self):
        """ validation for the amount field """
        cleaned_data = super(ManualTopup, self).clean()
        print(cleaned_data)
        if cleaned_data.get('amount'):
            amount = self.cleaned_data['amount']
            print(amount)
            if amount < 0:
                self._errors['amount'] = "Negative amounts are not allowed"
                if amount < AUTO_TOP_UP_MIN_AMT:
                    raise forms.ValidationError("Too small. Must be at least %s%s" %
                                                (GLOBAL_CURRENCY_SYMBOL,
                                                 AUTO_TOP_UP_MIN_AMT))
                if amount > AUTO_TOP_UP_MAX_AMT:
                    raise forms.ValidationError("Too large. Maximum is %s%s" %
                                                (GLOBAL_CURRENCY_SYMBOL,
                                                 AUTO_TOP_UP_MAX_AMT))
        else:
            self._errors['amount'] = "Please enter a value"

        return self.cleaned_data

    # def clean_amount(self):
    #     """ validation for the amount field """
    #     amount = self.cleaned_data['amount']
    #     if amount < 0:
    #         raise forms.ValidationError("Negative amounts are not allowed")
    #     if amount < AUTO_TOP_UP_MIN_AMT:
    #         raise forms.ValidationError("Too small. Must be at least %s%s" %
    #                                     (GLOBAL_CURRENCY_SYMBOL,
    #                                      AUTO_TOP_UP_MIN_AMT))
    #     if amount > AUTO_TOP_UP_MAX_AMT:
    #         raise forms.ValidationError("Too large. Maximum is %s%s" %
    #                                     (GLOBAL_CURRENCY_SYMBOL,
    #                                      AUTO_TOP_UP_MAX_AMT))
    #
    #     return amount
