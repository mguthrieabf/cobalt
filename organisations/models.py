from django.db import models
from django.conf import settings

class Organisation(models.Model):
    ORG_TYPE = [
        ('Club', 'Bridge Club'),
        ('State', 'State Association'),
        ('National', 'National Body'),
        ('Other', 'Other')
    ]
    org_id = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=50)
    type = models.CharField(choices=ORG_TYPE, max_length=8, blank="True", null=True)
    address1 = models.CharField(max_length=100, blank="True", null=True)
    address2 = models.CharField(max_length=100, blank="True", null=True)
    suburb = models.CharField(max_length=50, blank="True", null=True)
    state = models.CharField(max_length=3, blank="True", null=True)
    postcode = models.CharField(max_length=10, blank="True", null=True)

    def __str__(self):
        return self.name

class MemberOrganisation(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.member.full_name}, member of {self.organisation.name}"
