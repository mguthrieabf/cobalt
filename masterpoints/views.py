from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from .models import MasterpointsCopy, MasterpointDetails

@login_required(login_url='/accounts/login/')
def home(request):
    number = MasterpointsCopy.objects.count()
    return render(request, 'masterpoints/home.html', {'number' : number})

@login_required(login_url='/accounts/login/')
def masterpoints_detail(request,system_number):
    summary = MasterpointsCopy.objects.filter(abf_number = system_number)

# Get last year in YYYY-MM format
    dt = date.today()
    dt = dt.replace(year=dt.year-1)
    year = dt.strftime("%Y")
    month = dt.strftime("%m")

    details = MasterpointDetails.objects.filter(system_number = system_number,
                posting_date__gt="%s-%s" % (year, month)).order_by('-posting_date')
    counter = summary[0].total_MPs # we need to construct the balance to show
    gold = float(summary[0].total_gold)
    red = float(summary[0].total_red)
    green = float(summary[0].total_green)

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
        month = rolling_date.strftime("%m")
        labels_key.append("%s-%s" % (year, month))
        labels.append(rolling_date.strftime("%b"))
        rolling_date = rolling_date + relativedelta(months=+1)
        chart_gold["%s-%s" % (year, month)]=0.0
        chart_red["%s-%s" % (year, month)]=0.0
        chart_green["%s-%s" % (year, month)]=0.0


# loop through the details and augment the data to pass to the template
# we are just adding running total data for the table of details
    for d in details:
        counter = counter - d.mps

# we need to deduct the last entry from the opening total for all types
# just reset and work out which one it was later
        last_line_green = 0
        last_line_red = 0
        last_line_gold = 0

        d.running_total = counter
        if d.mp_colour == "Y":
            gold = gold - float(d.mps)
            last_line_gold = float(d.mps)
            chart_gold[d.posting_date]=chart_gold[d.posting_date]+float(d.mps)
        elif d.mp_colour == "R":
            red = red - float(d.mps)
            last_line_red = float(d.mps)
            chart_red[d.posting_date]=chart_red[d.posting_date]+float(d.mps)
        elif d.mp_colour == "G":
            green = green - float(d.mps)
            last_line_green = float(d.mps)
            chart_green[d.posting_date]=chart_green[d.posting_date]+float(d.mps)

# fill in the chart data
    running_gold = gold
    gold_series = []
    for l in reversed(labels_key):
        running_gold = running_gold - chart_gold[l]
        gold_series.append(float("%.2f" % running_gold))
    gold_series.reverse()

    running_red = red
    red_series = []
    for l in reversed(labels_key):
        running_gold = running_red - chart_red[l]
        red_series.append(float("%.2f" % running_red))
    red_series.reverse()

    running_green = green
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

    return render(request, 'masterpoints/details.html', {'details' : details,
                                                         'summary': summary[0],
                                                         'chart': chart,
                                                         'bottom': bottom})

def abf_lookup(request):
    if request.method == "GET":
        abf_number = request.GET['abf_number']
        member = MasterpointsCopy.objects.filter(abf_number = abf_number)
        if member:
            given_name = member[0].given_name
            surname = member[0].surname
            result = "%s %s" % (given_name, surname)
        else:
            result = "Invalid or inactive number"
        return render(request, 'masterpoints/abf_lookup.html', {'result' : result})

def get_masterpoints(abf_number):
    try:
        member = MasterpointsCopy.objects.filter(abf_number = abf_number)
        points = member[0].total_MPs
        rank = member[0].rank
    except:
        points = "Not found"
        rank = "Not found"
    return({'points' : points, 'rank': rank})
