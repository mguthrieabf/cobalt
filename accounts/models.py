from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    abf_number = models.IntegerField("ABF Number", blank="True", unique=True)
    mobile = models.IntegerField("Mobile Number", blank="True", unique=True, default="0")

    def __str__(self):
        return self.username
