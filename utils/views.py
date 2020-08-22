# from django.shortcuts import render
from geopy.geocoders import Nominatim
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import json


@login_required()
def geo_location(request, location):
    """ return lat and long for a text address """

    geolocator = Nominatim(user_agent="cobalt")
    loc = geolocator.geocode(location)
    html = {"lat": loc.latitude, "lon": loc.longitude}
    data_dict = {"data": html}
    return JsonResponse(data=data_dict, safe=False)


class CobaltBatch:
    """ Class to handle batch jobs within Cobalt. We use cron (or whatever you
    like) to trigger the jobs which are set up using django-extensions.

    Args:
        name(str) - name of this batch job
        schedule(str) - Daily, Hourly etc
        instance(str) - identifier for this run if runs can happen multiple time a day
        rerun(bool) - true to allow this to overwrite previous entry

    Returns:
        CobaltBatch
    """

    def __init__(self, name, schedule, instance=None, rerun=False):
        self.name = name
        self.schedule = schedule
        self.instance = instance
        self.rerun = rerun

    def finished(self, status="Success"):
        print("ok")
