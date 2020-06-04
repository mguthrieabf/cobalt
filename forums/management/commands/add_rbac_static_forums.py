from django.core.management.base import BaseCommand, CommandError
from rbac.models import (RBACGroup, RBACUserGroup, RBACGroupRole,
                         RBACModelDefault, RBACAppModelAction)

class Command(BaseCommand):

    def CreateRBACDefault(self, app, model):
        if not RBACModelDefault.objects.filter(app=app, model=model).exists():
            r = RBACModelDefault(app=app,
                                 model=model,
                                 default_behaviour="Allow")
            r.save()
            self.stdout.write(self.style.SUCCESS('RBACModelDefault created for %s.%s' % (app, model)))
        else:
            self.stdout.write(self.style.SUCCESS('RBACModelDefault already exists - ok'))

    def CreateRBACAction(self, app, model, action):
        if not RBACAppModelAction.objects.filter(app=app, model=model, valid_action=action).exists():
            r = RBACAppModelAction(app=app,
                                   model=model,
                                   valid_action=action)
            r.save()
            self.stdout.write(self.style.SUCCESS('Added %s.%s.%s to RBACAppModelAction' % (app, model, action)))
        else:
            self.stdout.write(self.style.SUCCESS('%s.%s.%s already in RBACAppModelAction. Ok.' % (app, model, action)))

    def handle(self, *args, **options):
        print("Running add_rbac_static")
        self.CreateRBACDefault("forums", "forum")
        self.CreateRBACAction("forums", "forum", "create")
        self.CreateRBACAction("forums", "forum", "delete")
        self.CreateRBACAction("forums", "forum", "view")
        self.CreateRBACAction("forums", "forum", "edit")
        self.CreateRBACAction("forums", "forum", "moderate")
