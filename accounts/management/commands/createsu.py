from django.core.management.base import BaseCommand, CommandError
from accounts.models import User

class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Running createsu")
        if not User.objects.filter(username="admin").exists():
            # User.objects.create_superuser("admin", "admin@admin.com", "admin")
            user = User.objects.create_user(username='admin',
                                 email='a@b.com',
                                 password='F1shcake',
                                 abf_number=99)
            user.is_superuser=True
            user.is_staff=True
            user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created new super user'))
        else:
            self.stdout.write(self.style.SUCCESS('admin user already exists - ok'))

        if not User.objects.filter(username="MG").exists():
            # User.objects.create_superuser("admin", "admin@admin.com", "admin")
            user = User.objects.create_user(username='MG',
                                 email='m@rkguthrie.com',
                                 password='F1shcake',
                                 abf_number=620246)
            user.is_superuser=True
            user.is_staff=True
            user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created new MG user'))
        else:
            self.stdout.write(self.style.SUCCESS('MG user already exists - ok'))
