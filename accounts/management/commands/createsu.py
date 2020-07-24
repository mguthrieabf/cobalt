from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    def CreateDefaultTestUsers(self, newuser, email, system_number, first, last):
        if not User.objects.filter(username=newuser).exists():
            user = User.objects.create_user(
                username=newuser,
                email=email,
                password="F1shcake",
                first_name=first,
                last_name=last,
                system_number=system_number,
            )
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS("Successfully created new super user - %s" % newuser)
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("%s user already exists - ok" % newuser)
            )

    def handle(self, *args, **options):
        print("Running createsu.")
        self.CreateDefaultTestUsers(
            "EVERYONE", "a@b.com", "0", "EVERYONE", "system_account"
        )
        self.CreateDefaultTestUsers(
            "Mark", "m@rkguthrie.com", "620246", "Mark", "Guthrie"
        )

        self.CreateDefaultTestUsers(
            "518891", "julianrfoster@gmail.com", "518891", "Julian", "Foster"
        )

        self.CreateDefaultTestUsers(
            "41841", "matmc@internode.on.net", "41841", "Matthew", "McManus"
        )

    #    self.CreateDefaultTestUsers("Neil", "nwilliams36@internode.on.net", "952281", "Neil", "Williams")
