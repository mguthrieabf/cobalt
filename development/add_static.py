import os

os.environ['DJANGO_SETTINGS_MODULE']='cobalt.settings'

import django
django.setup()

from django.contrib.auth import get_user_model
from payments.models import Balance


# see ref. below
UserModel = get_user_model()

user = UserModel.objects.create_user('Tubster', password='F1shcake', abf_number=620254, first_name='Julie', last_name = 'Guthrie', mobile=123456, email='m@rkguthrie.com')
user.save()
print("Added Tubster user")
user = UserModel.objects.create_user('MG', password='F1shcake', abf_number=620246, first_name='Mark', last_name = 'Guthrie', mobile=1234567, email='mark.guthrie@17ways.com.au')
user.save()
print("Added MG user")
user = UserModel.objects.create_user('Julian', password='F1shcake', abf_number=518891, first_name='Julian', last_name = 'Foster', mobile=12345678, email='mark.guthrie@sterlingrisq.com')
user.save()
print("Added Julian user")

b = Balance.objects.create(system_number = 620254, last_top_up_amount=200, balance = 154.23)
print("Added balance for Tubster")
b = Balance.objects.create(system_number = 620246, last_top_up_amount=100, balance = 204.00)
print("Added balance for MG")
b = Balance.objects.create(system_number = 518891, last_top_up_amount=250, balance = 321.00)
print("Added balance for Julian")
