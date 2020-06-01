""" Role Based Access Control Application

    This handles the models for role based security for Cobalt.

    See `RBAC Overview`_ for more details.

    .. _RBAC Overview:
       ./rbac_overview.html
"""
from django.db import models
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from accounts.models import User
from forums.models import Forum, Post, Comment1, Comment2
from organisations.models import Organisation
from django.apps import apps

class RBACGroup(models.Model):
    """ Group definitions """

    group_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.group_name

class RBACUserGroup(models.Model):
    """ Maps users to Groups """

    member = models.ForeignKey(User, on_delete=models.CASCADE)
    """ Standard User object """

    rbac_group = models.ForeignKey(RBACGroup, on_delete=models.CASCADE)
    """ RBAC Group """

    def __str__(self):
        return "%s - %s" % (self.rbac_group, self.member)

class RBACGroupRole(models.Model):
    """ Core model to map a group to a role. """

    group = models.ForeignKey(RBACGroup,
        on_delete=models.CASCADE
    )
    """ RBACGroup for this Role """

    role = models.CharField(max_length=50, unique=True)
    """ The role in dotted format. This is controlled by the Cobalt app that
    creates and uses it. Format should be <app>.<model>.<action> or
    <app>.<model>.<instance>.<action>
    """

    RULE_TYPES = [("Allow", "Allow User Access"), ("Block", "Blcok User Access")]
    rule_type = models.CharField(max_length=5,
        choices=RULE_TYPES,
        default="Allow"
    )
    """ Rules can Allow or Block permissions """

    def __str__(self):
        return '%s - %s - %s' % (self.group, self.role, self.rule_type)
