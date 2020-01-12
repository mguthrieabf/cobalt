import csv, sys, os
from pathlib import Path

os.environ['DJANGO_SETTINGS_MODULE']='cobalt.settings'

import django
django.setup()

from masterpoints.models import MasterpointsClubs

file = Path("development/MPClubs.tsv")

with open(file) as fp:
   line = fp.readline()   # skip first line headers
   line = fp.readline()
   while line:
        if line.find("rows affected")==-1:  # skip last row

            data=line.split('\t')
            print("Importing %s" % data[1])

            post=MasterpointsClubs()
            post.club_number = data[0]
            post.club_name = data[1]
            post.save()
        line = fp.readline()
