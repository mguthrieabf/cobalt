from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'system_number',
                  'mobile', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'system_number',
                  'dob', 'mobile', 'headline', 'about', 'pic', 'bbo_name',
                  'auto_amount', 'stripe_customer_id']

class BlurbUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['headline', 'about', 'pic']
