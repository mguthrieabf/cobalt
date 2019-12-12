import os
import django
import sys

sys.path.append(".")
os.environ["DJANGO_SETTINGS_MODULE"] = "cobalt.settings"

django.setup()

# your imports, e.g. Django models
from masterpoints.models import CurrentMPs

l=CurrentMPs()
l.abf="1233"
l.save()

abf=CurrentMPs.objects.all()
print(abf)

#import requests
#import zipfile

#print('Beginning file download with requests')

#url = 'http://abfmasterpoints.com.au/downloads/MPCData.zip'
#r = requests.get(url)

#with open('MCPData.zip', 'wb') as f:
#    f.write(r.content)

# with zipfile.ZipFile('MCPData.zip', 'r') as zip_ref:
#     zip_ref.extractall(".")
#
# f=open('MPData.csv')
#
# for line in f.readlines()[1:]:
#     print(line)
