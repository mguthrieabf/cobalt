""" Payment forms with validation """

from django import forms
from accounts.models import User
from organisations.models import Organisation
from cobalt.settings import (
    AUTO_TOP_UP_MIN_AMT,
    AUTO_TOP_UP_MAX_AMT,
    GLOBAL_CURRENCY_SYMBOL,
)
from .models import TRANSACTION_TYPE


class TestTransaction(forms.Form):
    """ Temporary - will be removed """

    amount = forms.DecimalField(label="Amount", max_digits=8, decimal_places=2)
    description = forms.CharField(label="Description", max_length=100)
    organisation = forms.ModelChoiceField(queryset=Organisation.objects.all())
    type = forms.ChoiceField(label="Transaction Type", choices=TRANSACTION_TYPE)
    url = forms.CharField(label="URL", max_length=100, required=False)


class MemberTransfer(forms.Form):
    """ M2M transfer form """

    transfer_to = forms.ModelChoiceField(queryset=User.objects.all())
    amount = forms.DecimalField(label="Amount", max_digits=8, decimal_places=2)
    description = forms.CharField(label="Description", max_length=100)

    # We need the logged in user to check the balance, add a parameter
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(MemberTransfer, self).__init__(*args, **kwargs)


class ManualTopup(forms.Form):
    """ Manual top up form """

    CARD_CHOICES = [
        ("Existing", "Use Registered Card"),
        ("Another", "Use Another Card"),
    ]

    amount = forms.DecimalField(label="Amount", max_digits=8, decimal_places=2)
    card_choice = forms.ChoiceField(
        label="Card Option", choices=CARD_CHOICES, required=False
    )

    def clean(self):
        """ validation for the amount field """
        cleaned_data = super(ManualTopup, self).clean()
        print(cleaned_data)
        if cleaned_data.get("amount"):
            amount = self.cleaned_data["amount"]
            if amount < AUTO_TOP_UP_MIN_AMT:
                txt = "x Insufficient amount. Minimum is %s%s" % (
                    GLOBAL_CURRENCY_SYMBOL,
                    AUTO_TOP_UP_MIN_AMT,
                )
                self._errors["amount"] = txt
                raise forms.ValidationError(txt)
            if amount > AUTO_TOP_UP_MAX_AMT:

                txt = "Too large. Maximum is %s%s" % (
                    GLOBAL_CURRENCY_SYMBOL,
                    AUTO_TOP_UP_MAX_AMT,
                )
                self._errors["amount"] = txt
                raise forms.ValidationError(txt)
        else:
            self._errors["amount"] = "Please enter a value"

        return self.cleaned_data
