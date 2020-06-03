""" Role Based Access Control Application

    This handles the models for role based security for Cobalt.

    See `RBAC Overview`_ for more details.

    .. _RBAC Overview:
       ./rbac_overview.html
"""
from django.db import models
#from django.contrib.contenttypes import fields
#from django.contrib.contenttypes.models import ContentType
from accounts.models import User
#from forums.models import Forum, Post, Comment1, Comment2
#from organisations.models import Organisation
#from django.apps import apps

RULE_TYPES = [("Allow", "Allow User Access"), ("Block", "Block User Access")]

class RBACGroup(models.Model):
    """ Group definitions """

    group_name = models.CharField(max_length=50)
    description = models.CharField(max_length=50)

    def __str__(self):
        return self.group_id

    @property
    def group_id(self):
        return "%s.%s - %s" % (self.group_name, self.id, self.description)

class RBACUserGroup(models.Model):
    """ Maps users to Groups """

    member = models.ForeignKey(User, on_delete=models.CASCADE)
    """ Standard User object """

    group = models.ForeignKey(RBACGroup, on_delete=models.CASCADE)
    """ RBAC Group """

    def __str__(self):
        return "%s - %s" % (self.group, self.member)

class RBACGroupRole(models.Model):
    """ Core model to map a group to a role. """

    group = models.ForeignKey(RBACGroup,
        on_delete=models.CASCADE
    )
    """ RBACGroup for this Role """

    app = models.CharField(max_length=15)
    """ Application level hierarchy """

    model = models.CharField(max_length=15)
    """ model level hierarchy """

    model_id = models.IntegerField(blank=True, null=True)
    """ Instance of model level hierarchy """

    action = models.CharField(max_length=15)
    """ What this role allows you to do here """

    rule_type = models.CharField(max_length=5,
        choices=RULE_TYPES,
        default="Allow"
    )
    """ Rules can Allow or Block permissions """

    def __str__(self):
        return '%s - %s - %s' % (self.group, self.role, self.rule_type)

    @property
    def role(self):
        "Returns the role in dotted format."
        if self.model_id:
            return '%s.%s.%s.%s' % (self.app, self.model, self.model_id, self.action)
        else:
            return '%s.%s.%s' % (self.app, self.model, self.action)

class RBACModelDefault(models.Model):
    """ Default behaviour for a model. Some models (e.g. forums.forum) need a
    default of allowing users access unless explicitly blocked. Other models
    (e.g. organisations.Organisation) need a default behaviour of blocking unless
    explicitly allowed. """
    app = models.CharField(max_length=15)
    """ Application level hierarchy """

    model = models.CharField(max_length=15)
    """ model level hierarchy """

    default_behaviour = models.CharField(max_length=5,
        choices=RULE_TYPES,
        default="Allow"
    )

    def __str__(self):
        return "%s.%s %s" % (self.app, self.model, self.default_behaviour)

class RBACAppModelAction(models.Model):
    """ Valid Actions for an App and Model combination """

    app = models.CharField(max_length=15)
    """ Application level hierarchy """

    model = models.CharField(max_length=15)
    """ model level hierarchy """

    valid_action = models.CharField(max_length=15)
    """ valid actions for this combination """
