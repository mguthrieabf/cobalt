import sys, os
from pathlib import Path

os.environ['DJANGO_SETTINGS_MODULE']='cobalt.settings'

import django
django.setup()

from masterpoints.models import MasterpointDetails

months=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

file = Path("development/MPDataDetails.tsv")

with open(file) as fp:
   line = fp.readline()   # skip first line headers
   line = fp.readline()
   while line:
       if line.find("rows affected")==-1:  # skip last row

            data=line.split('\t')

            post=MasterpointDetails()

            post.system_number = data[0]
            post.mps = data[1]
            post.posting_month = data[2]
            post.posting_year = data[3]
            post.mp_colour = data[4]
            post.event_description = data[5]
            post.event_code = data[6]
            post.posting_date = "%s-%02d" % (post.posting_year, int(post.posting_month))
            post.posting_date_display = "%s %s" % (months[int(post.posting_month)-1], post.posting_year)

            post.save()
       line = fp.readline()
