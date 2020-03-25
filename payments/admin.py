from django.contrib import admin
from .models import Balance, Transaction, Account

admin.site.register(Balance)
admin.site.register(Account)
admin.site.register(Transaction)
