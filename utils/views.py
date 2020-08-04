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
    html={"lat": loc.latitude, "lon": loc.longitude}
    data_dict = {"data": html}
    return JsonResponse(data=data_dict, safe=False)
