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

class UserApplication(models.Model):
    """ Core model to map a User to an Application model instance and a role.

    This uses GenericForeignKey to be able to map to any Cobalt app model as if
    it was a foreign key.

    - member is a User
    - model_content_type is a class within a model definition
    - model_id is an instance of model_content_type
    - model_instance is **TBA**
    - role is the permissioned role

    E.g.

    - Member: <John Smith>
    - model_content_type: "Forum" (=forums.views.Forum). Must match an import in rbac/models.py
    - model_id: 6 (forum with id=6)
    - role: forums.content.create (can create content in this forum)

    """

    member = models.ForeignKey(User,
        on_delete=models.CASCADE
    )
    """ Standard User object """

    model_content_type = models.ForeignKey(ContentType,
        on_delete=models.CASCADE
    )
    """ Maps to the model. Must be imported in rbac/models.py (this file) """

    model_id = models.PositiveIntegerField()
    """ id of the instance of this class model that this rule applies to """

    model_instance = fields.GenericForeignKey('model_content_type', 'model_id')
    """ To be better understood """

    role = models.CharField(max_length=50)
    """ The role in dotted format. This is controlled by the Cobalt app that
    creates and uses it. Format should be <app>.<noun>.<action>
    """

    RULE_TYPES = [("Allow", "Allow User Access"), ("Block", "Blcok User Access")]
    rule_type = models.CharField(max_length=5,
        choices=RULE_TYPES,
        default="Allow"
    )

    def __str__(self):
        return '%s - %s - %s' % (self.member, self.model_content_type, self.model_id)

    def create_cobalt_rbac_mapping(member, app_name, model_name, model_id, rule_type, role):
        """ Create an RBAC record

        Create RBAC entry.

        Args:
            member(User): standard user object
            app_name(str): name of the application
            model_name(str): name of the application model class
            model_id(int): primary key for the instance of model_name this rule applies for
            role(str): dot format role <app>.<noun>.<action>
            rule_type(str): Allow or Block

        Returns:
            Nothing.
        """
        model = ContentType.objects.get(app_label=app_name, model=model_name)
        rule = UserApplication(member=member, model_content_type=model, model_id=model_id, role=role, rule_type=rule_type)
        rule.save()
        print(rule)

    def user_role_for_object(member, app_name, model_name, model_id):
        """ Return an RBAC record

        Args:
            member(User): standard user object
            app_name(str): name of the application
            model_name(str): name of the application model class
            model_id(int): primary key for the instance of model_name this rule applies for

        Returns:
            role(str): dot format role <app>.<noun>.<action>. Or None.
        """

        model = ContentType.objects.get(app_label=app_name, model=model_name)
        matches = UserApplication.objects.filter(member=member, model_content_type=model, model_id=model_id)

        print("Instance level rules:")
        print(matches)
        matches_up = UserApplication.objects.filter(member=member, model_content_type=model, model_id=None)
        print("High level rules:")
        print(matches_up)


        return matches
