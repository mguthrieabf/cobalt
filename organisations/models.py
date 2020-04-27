from django.db import models
from django.conf import settings

class Organisation(models.Model):
    ORG_TYPE = [
        ('Club', 'Bridge Club'),
        ('State', 'State Association'),
        ('National', 'National Body'),
        ('Other', 'Other')
    ]
    org_id = models.CharField(max_length=4)
    name = models.CharField(max_length=50)
    type = models.CharField(choices=ORG_TYPE, max_length=8, null=True)
    address1 = models.CharField(max_length=30, null=True)
    address2 = models.CharField(max_length=30, null=True)
    address3 = models.CharField(max_length=30, null=True)
    state = models.CharField(max_length=3, null=True)
    postcode = models.CharField(max_length=6, null=True)

class MemberOrganisation(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
