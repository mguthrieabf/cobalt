import csv, sys, os
from pathlib import Path

os.environ['DJANGO_SETTINGS_MODULE']='cobalt.settings'

import django
django.setup()

from masterpoints.models import MasterpointsCopy

file = Path("development/MPData.csv")

data = csv.reader(open(file),delimiter=",")
count=0
for row in data:
    count=count+1
    if count==1:
        continue

    post=MasterpointsCopy()
    post.abf_number = row[0]
    post.surname = row[1]
    post.given_name = row[2]
    post.home_club = row[3]
    post.rank  = row[4]
    post.gender = row[5]
    if row[6]=="Y":
        post.active=True
    else:
        post.active=False
    post.total_MPs = row[7]
    post.total_gold = row[8]
    post.total_red = row[9]
    post.total_green = row[10]
    post.month_total = row[11]
    post.month_gold = row[12]
    post.month_red = row[13]
    post.month_green = row[14]
    post.this_year = row[15]
    post.last_year = row[16]
    post.prior = row[17]
    post.pre82_red = row[18]
    post.year_start_rank = row[19]
    post.current_rank_seq = row[20]
    post.year_start_rank_seq = row[21]
    post.last_promotion_date = row[22]

    if post.active==True:
        post.save()
