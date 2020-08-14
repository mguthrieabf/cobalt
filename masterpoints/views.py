from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from accounts.models import User
import requests
import calendar
import html
from cobalt.settings import GLOBAL_MPSERVER

#####
#
# This module is a little strange as it gets all of its data from
# an external source, not from our database.
#
# We use requests to access a node.js web service which connects
# to a SQL Server database. Confluence can tell you more
#
######


@login_required()
def masterpoints_detail(request, system_number=None):

    if system_number is None:
        system_number = request.user.system_number

    # Get summary data
    qry = "%s/mps/%s" % (GLOBAL_MPSERVER, system_number)
    try:
        r = requests.get(qry).json()
    except (
        IndexError,
        requests.exceptions.InvalidSchema,
        requests.exceptions.MissingSchema,
        ConnectionError,
    ):
        r = []
    if len(r) == 0:
        error_msg = "No entry found for %s" % system_number
        error = {"cobalt_error_msg": error_msg}
        raise Http404(error)
    summary = r[0]

    # Set active to a boolean
    if summary["IsActive"] == "Y":
        summary["IsActive"] = True
    else:
        summary["IsActive"] = False

    # Get home club name
    qry = "%s/club/%s" % (GLOBAL_MPSERVER, summary["HomeClubID"])
    club = requests.get(qry).json()[0]["ClubName"]

    # Get last year in YYYY-MM format
    dt = date.today()
    dt = dt.replace(year=dt.year - 1)
    year = dt.strftime("%Y")
    month = dt.strftime("%m")

    # Get the detail list of recent activity
    qry = "%s/mpdetail/%s/postingyear/%s/postingmonth/%s" % (
        GLOBAL_MPSERVER,
        system_number,
        year,
        month,
    )
    details = requests.get(qry).json()

    counter = summary["TotalMPs"]  # we need to construct the balance to show
    gold = float(summary["TotalGold"])
    red = float(summary["TotalRed"])
    green = float(summary["TotalGreen"])

    # build list for the fancy chart at the top while we loop through.
    labels_key = []
    labels = []
    chart_green = {}
    chart_red = {}
    chart_gold = {}

    # build chart labels
    # go back a year then move forward
    rolling_date = datetime.today() + relativedelta(years=-1)

    for i in range(13):
        year = rolling_date.strftime("%Y")
        month = rolling_date.strftime("%m")
        labels_key.append("%s-%s" % (year, month))
        labels.append(rolling_date.strftime("%b"))
        rolling_date = rolling_date + relativedelta(months=+1)
        chart_gold["%s-%s" % (year, month)] = 0.0
        chart_red["%s-%s" % (year, month)] = 0.0
        chart_green["%s-%s" % (year, month)] = 0.0

    last_line_green = 0
    last_line_red = 0
    last_line_gold = 0

    # loop through the details and augment the data to pass to the template
    # we are just adding running total data for the table of details
    for d in details:
        counter = counter - d["mps"]

        # we need to deduct the last entry from the opening total for all types
        # just reset and work out which one it was later
        last_line_green = 0
        last_line_red = 0
        last_line_gold = 0

        d["running_total"] = counter
        d["PostingDate"] = "%s-%s" % (d["PostingYear"], d["PostingMonth"])
        d["PostingDateDisplay"] = "%s-%s" % (
            calendar.month_abbr[d["PostingMonth"]],
            d["PostingYear"],
        )

        # Its too slow to filter at the db so skip any month we don't want
        if not d["PostingDate"] in chart_gold:
            continue

        if d["MPColour"] == "Y":
            gold = gold - float(d["mps"])
            last_line_gold = float(d["mps"])
            chart_gold[d["PostingDate"]] = chart_gold[d["PostingDate"]] + float(
                d["mps"]
            )
        elif d["MPColour"] == "R":
            red = red - float(d["mps"])
            last_line_red = float(d["mps"])
            chart_red[d["PostingDate"]] = chart_red[d["PostingDate"]] + float(d["mps"])
        elif d["MPColour"] == "G":
            green = green - float(d["mps"])
            last_line_green = float(d["mps"])
            chart_green[d["PostingDate"]] = chart_green[d["PostingDate"]] + float(
                d["mps"]
            )

    # fill in the chart data
    running_gold = float(summary["TotalGold"])
    gold_series = []
    for l in reversed(labels_key):
        running_gold = running_gold - chart_gold[l]
        gold_series.append(float("%.2f" % running_gold))
    gold_series.reverse()

    running_red = float(summary["TotalRed"])
    red_series = []
    for l in reversed(labels_key):
        running_red = running_red - chart_red[l]
        red_series.append(float("%.2f" % running_red))
    red_series.reverse()

    running_green = float(summary["TotalGreen"])
    green_series = []
    for l in reversed(labels_key):
        running_green = running_green - chart_green[l]
        green_series.append(float("%.2f" % running_green))
    green_series.reverse()

    chart = {
        "labels": labels,
        "gold": gold_series,
        "red": red_series,
        "green": green_series,
    }

    # update bottom line
    total = "%.2f" % (
        green + red + gold - last_line_gold - last_line_red - last_line_green
    )
    green = "%.2f" % (green - last_line_green)
    red = "%.2f" % (red - last_line_red)
    gold = "%.2f" % (gold - last_line_gold)

    bottom = {"gold": gold, "red": red, "green": green, "total": total}

    return render(
        request,
        "masterpoints/details.html",
        {
            "details": details,
            "summary": summary,
            "club": club,
            "chart": chart,
            "bottom": bottom,
        },
    )


@login_required()
def masterpoints_search(request):
    if request.method == "POST":
        system_number = request.POST["system_number"]
        last_name = request.POST["last_name"]
        first_name = request.POST["first_name"]
        if system_number:
            return redirect("view/%s/" % system_number)
        else:
            if not first_name:  # last name only
                matches = requests.get(
                    "%s/lastname_search/%s" % (GLOBAL_MPSERVER, last_name)
                ).json()
            elif not last_name:  # first name only
                matches = requests.get(
                    "%s/firstname_search/%s" % (GLOBAL_MPSERVER, first_name)
                ).json()
            else:  # first and last names
                matches = requests.get(
                    "%s/firstlastname_search/%s/%s"
                    % (GLOBAL_MPSERVER, first_name, last_name)
                ).json()
            if len(matches) == 1:
                system_number = matches[0]["ABFNumber"]
                return redirect("view/%s/" % system_number)
            else:
                return render(
                    request,
                    "masterpoints/masterpoints_search_results.html",
                    {"matches": matches},
                )
    else:
        return redirect("view/%s/" % request.user.system_number)


def system_number_lookup(request):
    """
    Called from the registration page. Takes in a system number and returns
    the member first and lastname or an error message.
    """
    if request.method == "GET":
        system_number = request.GET["system_number"]
        member = None
        result = "Error: Invalid or inactive number"
        if system_number.isdigit():
            try:
                member = requests.get(
                    "%s/id/%s" % (GLOBAL_MPSERVER, system_number)
                ).json()[0]
            except IndexError:
                member = None

        if member:
            m = User.objects.filter(system_number=system_number)
            if m:  # already registered
                result = "Error: User already registered"
            else:
                if member["IsActive"] == "Y":
                    given_name = member["GivenNames"]
                    surname = member["Surname"]
                    result = "%s %s" % (given_name, surname)
                    # convert special chars
                    result = html.unescape(result)

    return HttpResponse(result)


def system_number_available(system_number):
    """
    Called from the registration page. Takes in a system number and returns
    True if number is valid and available
    """

    if system_number.isdigit():
        try:
            match = requests.get("%s/id/%s" % (GLOBAL_MPSERVER, system_number)).json()[
                0
            ]
        except IndexError:
            return False

    if match:
        member = User.objects.filter(system_number=system_number)
        if member:  # already registered
            return False
        else:
            if match["IsActive"] == "Y":
                return True
    return False


def get_masterpoints(system_number):
    # Called from Dashboard
    try:
        summary = requests.get("%s/mps/%s" % (GLOBAL_MPSERVER, system_number)).json()[0]
        points = summary["TotalMPs"]
        rank = summary["RankName"] + " Master"
    except (
        IndexError,
        requests.exceptions.InvalidSchema,
        requests.exceptions.MissingSchema,
        ConnectionError,
    ):
        points = "Not found"
        rank = "Not found"
    return {"points": points, "rank": rank}
