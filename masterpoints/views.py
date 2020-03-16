from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from accounts.models import User
import requests
import calendar
from cobalt.settings import GLOBAL_MPSERVER

@login_required(login_url='/accounts/login/')
def masterpoints_detail(request, system_number=None):

   if system_number == None:
       system_number = request.user.abf_number

   summary = requests.get('%s/mps/%s' % (GLOBAL_MPSERVER, system_number)).json()[0]
   club_string = summary['HomeClubID']
   club = requests.get('%s/club/%s' % (GLOBAL_MPSERVER, club_string)).json()[0]['ClubName']
# Get last year in YYYY-MM format
   dt = date.today()
   dt = dt.replace(year=dt.year-1)
   year = dt.strftime("%Y")
   month = dt.strftime("%-m")

   details = requests.get('%s/mpdetail/%s/postingyear/%s/postingmonth/%s' %
        (GLOBAL_MPSERVER, system_number, year, month)).json()
   counter = summary['TotalMPs'] # we need to construct the balance to show
   gold = float(summary['TotalGold'])
   red = float(summary['TotalRed'])
   green = float(summary['TotalGreen'])

# build list for the fancy chart at the top while we loop through
   labels_key=[]
   labels=[]
   chart_green={}
   chart_red={}
   chart_gold={}

# build chart labels
   rolling_date = datetime.today() + relativedelta(years=-1) # go back a year then move forward

   for i in range(13):
       year = rolling_date.strftime("%Y")
       month = rolling_date.strftime("%-m")
       labels_key.append("%s-%s" % (year, month))
       labels.append(rolling_date.strftime("%b"))
       rolling_date = rolling_date + relativedelta(months=+1)
       chart_gold["%s-%s" % (year, month)]=0.0
       chart_red["%s-%s" % (year, month)]=0.0
       chart_green["%s-%s" % (year, month)]=0.0

   # last_line_green = 0
   # last_line_red = 0
   # last_line_gold = 0

# loop through the details and augment the data to pass to the template
# we are just adding running total data for the table of details
   for d in details:
       counter = counter - d['mps']

# we need to deduct the last entry from the opening total for all types
# just reset and work out which one it was later
       last_line_green = 0
       last_line_red = 0
       last_line_gold = 0

       d["running_total"] = counter
       d["PostingDate"] = "%s-%s" % (d["PostingYear"], d["PostingMonth"])
       d["PostingDateDisplay"] = "%s-%s" % (calendar.month_abbr[d["PostingMonth"]], d["PostingYear"])

       if not d["PostingDate"] in chart_gold:
           continue

       if d['MPColour'] == "Y":
           gold = gold - float(d['mps'])
           last_line_gold = float(d['mps'])
           chart_gold[d['PostingDate']]=chart_gold[d['PostingDate']]+float(d['mps'])
       elif d['MPColour'] == "R":
           red = red - float(d['mps'])
           last_line_red = float(d['mps'])
           chart_red[d['PostingDate']]=chart_red[d['PostingDate']]+float(d['mps'])
       elif d['MPColour'] == "G":
           green = green - float(d['mps'])
           last_line_green = float(d['mps'])
           chart_green[d['PostingDate']]=chart_green[d['PostingDate']]+float(d['mps'])

# fill in the chart data
   running_gold = float(summary['TotalGold'])
   gold_series = []
   for l in reversed(labels_key):
       running_gold = running_gold - chart_gold[l]
       gold_series.append(float("%.2f" % running_gold))
   gold_series.reverse()

   running_red = float(summary['TotalRed'])
   red_series = []
   for l in reversed(labels_key):
       running_red = running_red - chart_red[l]
       red_series.append(float("%.2f" % running_red))
   red_series.reverse()

   running_green = float(summary['TotalGreen'])
   green_series = []
   for l in reversed(labels_key):
       running_green = running_green - chart_green[l]
       green_series.append(float('%.2f' % running_green))
   green_series.reverse()


   chart = {'labels': labels,
            'gold': gold_series,
            'red': red_series,
            'green': green_series
           }

# update bottom line
   total = "%.2f" % (green + red + gold - last_line_gold - last_line_red - last_line_green)
   green = "%.2f" % (green - last_line_green)
   red = "%.2f" % (red - last_line_red)
   gold = "%.2f" % (gold - last_line_gold)

   bottom = {'gold': gold, 'red': red, 'green': green, 'total': total}

   return render(request, 'masterpoints/details.html', {'details': details,
                                                        'summary': summary,
                                                        'club': club,
                                                        'chart': chart,
                                                        'bottom': bottom})

@login_required(login_url='/accounts/login/')
def masterpoints_search(request):
   if request.method == 'POST':
       system_number = request.POST['system_number']
       last_name = request.POST['last_name']
       first_name = request.POST['first_name']
       if system_number:
           return redirect("view/%s/" % system_number)
       else:
           if not first_name: # last name only
               matches = MasterpointsCopy.objects.filter(surname__icontains = last_name)
           elif not last_name: # first name only
               matches = MasterpointsCopy.objects.filter(given_name__iexact = first_name)
           else: # first and last names
               matches = MasterpointsCopy.objects.filter(given_name__iexact = first_name, surname__icontains = last_name)
           if len(matches)==1:
               system_number=matches[0].abf_number
               return redirect("view/%s/" % system_number)
           else:
               # clubs = MasterpointsClubs.objects.filter(club_number = )
               return render(request,
                   'masterpoints/masterpoints_search_results.html',
                   {'matches' : matches})
   else:
       return redirect("view/%s/" % request.user.abf_number)

def abf_lookup(request):
   if request.method == "GET":
       abf_number = request.GET['abf_number']
       member=None
       if abf_number.isdigit():
           try:
               member = requests.get('%s/id/%s' % (GLOBAL_MPSERVER, abf_number)).json()[0]
           except:
               member=None
       result = "Invalid or inactive number"
       if member:
           if member["IsActive"]=="Y":
               given_name = member["GivenNames"]
               surname = member["Surname"]
               result = "%s %s" % (given_name, surname)

       return render(request, 'masterpoints/abf_lookup.html', {'result' : result})

def get_masterpoints(abf_number):

   try:
       summary = requests.get('%s/mps/%s' % (GLOBAL_MPSERVER, abf_number)).json()[0]
       points = summary["TotalMPs"]
       rank = summary["RankName"]
   except:
       points = "Not found"
       rank = "Not found"
   return({'points' : points, 'rank': rank})
