from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# from django.utils.translation import ugettext_lazy as _
# from django.db.models.signals import post_save

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    confirmed = models.BooleanField("Confirmed", default=False)

    abf_number = models.IntegerField("ABF Number", blank="True", default="0")
    mobile = models.IntegerField("Mobile Number", blank="True", default="0")
    # city = models.CharField("City", max_length=50, blank=True)
    # state = models.CharField("State", max_length=50, blank=True)
    # country = models.CharField("Country", max_length=50, blank=True)
    # referral = models.CharField("Referral", max_length=50, blank=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# def save(self, *args, **kwargs):
#     super().save(*args, **kwargs)
