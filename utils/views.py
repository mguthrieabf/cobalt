# from django.shortcuts import render
from geopy.geocoders import Nominatim
from django.contrib.auth.decorators import login_required


@login_required()
def geo_location(request):
    """ return lat and long for a text address """

    if request.method == "POST":
        if "address" in request.POST:
            address = request.POST["address"]
            geolocator = Nominatim(user_agent="cobalt")
            location = geolocator.geocode(address)
            print(location.latitude, location.longitude)
