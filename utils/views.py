# from django.shortcuts import render
from geopy.geocoders import Nominatim
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import json

# @login_required()
def geo_location(request):
    """ return lat and long for a text address """
    print("inside")
    if request.method == "POST":
        print("POST")
        x = request.POST.get('data', 'nutin')
        print(x)
#        data = json.loads(request.POST.get('location', ''))
        data = request.POST.get('location', '')
        print("=%s=" % data)
        if "address" in request.POST:
            address = request.POST["address"]
            geolocator = Nominatim(user_agent="cobalt")
            location = geolocator.geocode(address)
            print(location.latitude, location.longitude)

    return HttpResponse("hello")
