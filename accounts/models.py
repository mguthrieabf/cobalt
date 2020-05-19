from django.db import models
from django.contrib.auth.models import AbstractUser
from cobalt.settings import GLOBAL_ORG
from django.core.validators import MaxValueValidator
from cobalt.settings import AUTO_TOP_UP_MAX_AMT

class User(AbstractUser):
    """
    User class based upon AbstractUser.
    """
    email = models.EmailField(unique=False)
    system_number = models.IntegerField("%s Number" % GLOBAL_ORG, blank=True, unique=True)
    mobile = models.IntegerField("Mobile Number", blank=True, unique=True, null=True)
    headline = models.TextField("Headline", blank=True, null=True, default="Not filled in", max_length=100)
    about = models.TextField("About Me", blank=True, null=True, default="Not filled in", max_length=800)
    pic = models.ImageField(upload_to = 'pic_folder/', default = 'pic_folder/default-avatar.png')
    dob = models.DateField(blank="True", null=True)
    bbo_name = models.CharField("BBO Username", blank=True, null=True, max_length=20)
    auto_amount = models.PositiveIntegerField("Auto Top Up Amount", blank=True,
    null=True, validators=[MaxValueValidator(AUTO_TOP_UP_MAX_AMT)])
    stripe_customer_id = models.CharField("Stripe Customer Id", blank=True, null=True, max_length=25)
    stripe_auto_confirmed = models.BooleanField(blank=True, null=True)

    REQUIRED_FIELDS = ['system_number', 'email'] # tells createsuperuser to ask for them

    def __str__(self):
        return "%s - %s" % (self.system_number, self.full_name)

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)
