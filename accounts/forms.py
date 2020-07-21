""" Forms for Accounts App """

from django import forms
from django.contrib.auth.forms import UserCreationForm
from masterpoints.views import system_number_available
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

    def clean_username(self):
        """ check system_number is valid. Don't rely on client side validation """
        print("inside")
        username = self.cleaned_data["username"]
        if username:
            if not system_number_available(username):
                raise forms.ValidationError("Number invalid or in use")
        else:
            raise forms.ValidationError("System number missing")

        return username


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
            "about",
            "pic",
            "bbo_name",
        ]


class BlurbUpdateForm(forms.ModelForm):
    """ Handles the sub-form on profile for picture and wordage """

    class Meta:
        """ Meta data """

        model = User
        fields = ["about", "pic"]
