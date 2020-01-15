from django.core.management.base import BaseCommand, CommandError
from accounts.models import User

class Command(BaseCommand):

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            # User.objects.create_superuser("admin", "admin@admin.com", "admin")
            user = User.objects.create_user(username='admin',
                                 email='a@b.com',
                                 password='F1shcake',
                                 abf_number=99)
            self.stdout.write(self.style.SUCCESS('Successfully created new super user'))
