from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from logs.views import log_event

# This allows logins using either abf no, userid or email address

class CobaltBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        UserModel = get_user_model()

# Try email address, then username, then abf_number

        con_type = "Unknown"

        try:
            user = UserModel.objects.get(email=username)
            con_type = "email"
        except UserModel.DoesNotExist:
            try:
                user = UserModel.objects.get(username=username)
                con_type = "username"
            except UserModel.DoesNotExist:
                try:
                    if username.isdigit():
                        user = UserModel.objects.get(abf_number=username)
                        con_type = "ABF Number"
                    else:
                        user = None
                except UserModel.DoesNotExist:
                    user = None

        if user==None:
            log_event(request, "Login" , "WARN",
                        "Accounts", "Login", "Login failed - unknown userid")
            return None

        if user.check_password(password):
            log_event(request, "%s %s" % (user.first_name, user.last_name) , "INFO",
                        "Accounts", "Login", "Logged in using %s" % con_type)
            return user
