from django.core.management.base import BaseCommand, CommandError
from accounts.models import User

class Command(BaseCommand):
    """
    I need the masterpoints file Alternat.txt to be in the parent directory.
    You can get this from abfmasterpoints.com.au
    """

    def CreateDefaultTestUsers(self, newuser, email, system_number, first, last):
        if not User.objects.filter(username=newuser).exists():
            user = User.objects.create_user(username=newuser,
                                 email=email,
                                 password='F1shcake',
                                 first_name=first,
                                 last_name=last,
                                 system_number=system_number)
            user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created new user - %s %s(%s)' % (first, last, newuser)))
        else:
            self.stdout.write(self.style.SUCCESS('%s user already exists - ok' % newuser))

    def handle(self, *args, **options):
        print("Running createdummyusers.")
        with open("../Alternat.txt") as f:
            for line in f:
                parts=line.strip().split()
                system_number = parts[0]
                second = parts[1]
                first = parts[2]
                self.CreateDefaultTestUsers(system_number, "%s@fake.com" % system_number, system_number, first, second)
