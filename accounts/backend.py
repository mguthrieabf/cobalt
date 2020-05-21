""" This module implements the login function. This is customised to allow
    users to login using either their email address or system_number.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from logs.views import log_event

# This allows logins using either system no, userid or email address

class CobaltBackend(ModelBackend):
    """ Custom backend to control user logins. """

    def authenticate(self, request, username=None, password=None):
        """ method to authenticate users """

        UserModel = get_user_model()

# Try email address, then username, then system_number

        con_type = "Unknown"

        try:
            user = UserModel.objects.filter(email=username).first()
            con_type = "email"
        except IndexError:
            try:
                user = UserModel.objects.get(username=username)
                con_type = "username"
            except UserModel.DoesNotExist:
                try:
                    if username.isdigit():
                        user = UserModel.objects.get(system_number=username)
                        con_type = "System Number"
                    else:
                        user = None
                except UserModel.DoesNotExist:
                    user = None

        if user is None:
            log_event(request=request,
                      user="Login",
                      severity="WARN",
                      source="Accounts",
                      sub_source="Login",
                      message="Login failed - unknown userid")

            return None

        if user.check_password(password):
            log_event(request=request,
                      user=user.full_name,
                      severity="INFO",
                      source="Accounts",
                      sub_source="Login",
                      message="Logged in using %s" % con_type)

            return user
        return None
