from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    location = models.CharField(max_length=30)
    age = models.IntegerField()
    wage = models.IntegerField()

    def ___str___(self):
        return self.user.username
