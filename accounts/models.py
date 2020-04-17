from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=False)
    abf_number = models.IntegerField("ABF Number", blank="True", unique=True)
    mobile = models.IntegerField("Mobile Number", blank="True", unique=True, null=True)
    headline = models.TextField("Headline", blank="True", null=True, default="Not filled in", max_length=100)
    about = models.TextField("About Me", blank="True", null=True, default="Not filled in", max_length=800)
    pic = models.ImageField(upload_to = 'pic_folder/', default = 'pic_folder/default-avatar.png')
    dob = models.DateField(blank="True", null=True)
    bbo_name = models.TextField("BBO Username", blank="True", null=True, max_length=20)


    REQUIRED_FIELDS = ['abf_number', 'email'] # tells createsuperuser to ask for them

    def __str__(self):
        return "%s - %s" % (self.abf_number, self.full_name)

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)
