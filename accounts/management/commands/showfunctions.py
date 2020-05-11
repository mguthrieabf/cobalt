from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('application', help="Name of application to scan.", type=str)

    def print_functions(self, fname):
        with open(fname) as fn:
            lines = fn.readlines()
            lnumber = 0
            for line in lines:
                lnumber+=1

                if line.lower().startswith("def "): # found a function
                    output=line[4:]
                    self.stdout.write(f"{lnumber}")
                    if lines[lnumber].find('"""'):
                        self.stdout.write("Found a comment")
                    self.stdout.write(line)

    def handle(self, *args, **options):
        application = options['application']
        self.print_functions(f"{application}/views.py")
