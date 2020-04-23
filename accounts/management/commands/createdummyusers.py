from django.core.management.base import BaseCommand, CommandError
from accounts.models import User

class Command(BaseCommand):

    def CreateDefaultTestUsers(self, newuser, email, abf, first, last):
        print(newuser)
        print(email)
        print(abf)
        print(first)
        print(last)
        if not User.objects.filter(username=newuser).exists():
            user = User.objects.create_user(username=newuser,
                                 email=email,
                                 password='F1shcake',
                                 first_name=first,
                                 last_name=last,
                                 abf_number=abf)
            user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created new user - %s' % newuser))
        else:
            self.stdout.write(self.style.SUCCESS('%s user already exists - ok' % newuser))

    def handle(self, *args, **options):
        print("Running createdummyusers.")
        with open("../Alternat.txt") as f:
            for line in f:
                parts=line.strip().split()
                abf_number = parts[0]
                second = parts[1]
                first = parts[2]
                self.CreateDefaultTestUsers(abf_number, "%s@fake.com" % abf_number, abf_number, first, second)
