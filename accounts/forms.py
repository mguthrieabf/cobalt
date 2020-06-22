""" Forms for Accounts App """

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegisterForm(UserCreationForm):
    """ User Registration """

    email = forms.EmailField()

    class Meta:
        """ Meta data """

        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "system_number",
            "mobile",
            "password1",
            "password2",
        ]


class UserUpdateForm(forms.ModelForm):
    """ Used by Profile to update details """

    class Meta:
        """ Meta data """

        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "system_number",
            "dob",
            "mobile",
            "headline",
            "about",
            "pic",
            "bbo_name",
        ]


class BlurbUpdateForm(forms.ModelForm):
    """ Handles the sub-form on profile for picture and wordage """

    class Meta:
        """ Meta data """

        model = User
        fields = ["headline", "about", "pic"]
