from django.core.management.base import BaseCommand, CommandError
from organisations.models import Organisation

class Command(BaseCommand):
    """
    I need the masterpoints file ClubsData.csv to be in the parent directory.
    You can get this from abfmasterpoints.com.au
    """

    def CreateClubs(self, org_id, name, address1, address2, address3,
                        state, postcode, type):
        org = Organisation(org_id = org_id,
                           name = name,
                           address1 = address1,
                           address2 = address2,
                           suburb = address3,
                           state = state,
                           type = type,
                           postcode = postcode)
        org.save()
        self.stdout.write(self.style.SUCCESS('Successfully created new club - %s %s' % (org_id, name)))

    def handle(self, *args, **options):
        print("Running importclubs.")
        first_line = True
        with open("../ClubsData.csv") as f:
            for line in f:
                print(line)
                if first_line:
                    first_line = False
                    continue
                parts=line.strip().split(',')
                org_id = parts[0]
                name = parts[1]
                address1 = parts[2]
                address2 = parts[3]
                address3 = parts[4]
                state = parts[5]
                postcode = parts[6]
                type = 'Club'
                self.CreateClubs(org_id, name, address1, address2, address3,
                                    state, postcode, type)
