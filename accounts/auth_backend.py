from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class OurBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username.find("@")>=1:   # Email address
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                return None
            else:
                if user.check_password(password):
                    return user
        elif username.isdigit():   # ABF number
            try:
                user = UserModel.objects.get(abf_number=username)
            except UserModel.DoesNotExist:
                return None
            else:
                if user.check_password(password):
                    return user
        else:   # username
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                return None
            else:
                if user.check_password(password):
                    return user
        return None
