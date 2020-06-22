""" Models for our definitions of a user within the system. """

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, RegexValidator
from cobalt.settings import AUTO_TOP_UP_MAX_AMT, GLOBAL_ORG


class User(AbstractUser):
    """
    User class based upon AbstractUser.
    """

    email = models.EmailField(unique=False)
    system_number = models.IntegerField(
        "%s Number" % GLOBAL_ORG, blank=True, unique=True
    )

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    mobile = models.CharField(
        "Mobile Number",
        blank=True,
        unique=True,
        null=True,
        max_length=15,
        validators=[phone_regex],
    )
    headline = models.TextField(
        "Headline", blank=True, null=True, default="Not filled in", max_length=100
    )
    about = models.TextField(
        "About Me", blank=True, null=True, default="Not filled in", max_length=800
    )
    pic = models.ImageField(
        upload_to="pic_folder/", default="pic_folder/default-avatar.png"
    )
    dob = models.DateField(blank="True", null=True)
    bbo_name = models.CharField("BBO Username", blank=True, null=True, max_length=20)
    auto_amount = models.PositiveIntegerField(
        "Auto Top Up Amount",
        blank=True,
        null=True,
        validators=[MaxValueValidator(AUTO_TOP_UP_MAX_AMT)],
    )
    stripe_customer_id = models.CharField(
        "Stripe Customer Id", blank=True, null=True, max_length=25
    )
    stripe_auto_confirmed = models.BooleanField(blank=True, null=True)

    REQUIRED_FIELDS = [
        "system_number",
        "email",
    ]  # tells createsuperuser to ask for them

    def __str__(self):
        return "%s(%s: %s)" % (self.full_name, GLOBAL_ORG, self.system_number)

    @property
    def full_name(self):
        "Returns the person's full name."
        return "%s %s" % (self.first_name, self.last_name)
