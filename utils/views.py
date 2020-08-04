# from django.shortcuts import render
from geopy.geocoders import Nominatim
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import json

@login_required()
def geo_location(request, location):
    """ return lat and long for a text address """

    print(location)

    # if request.method == "POST":
    #
    #     print(request.body)
    #     # print(request.POST.get('location'))
    #     # print(request.body['location'])
    #     data = json.loads(request.body)
    #     print(data)
    #    # response_json = request.POST
       # response_json = json.dumps(response_json)
       # data = json.loads(response_json)
       # print(data)
       #  # data = request.body.decode('utf-8')
        # print("=%s=" % data)
        # data = json.loads(request.POST.get('data', ''))
        # print("=%s=" % data)
        # if "address" in request.POST:
        #     address = request.POST["address"]
        #     geolocator = Nominatim(user_agent="cobalt")
        #     location = geolocator.geocode(address)
        #     print(location.latitude, location.longitude)

    return HttpResponse({"status": "hello"})
