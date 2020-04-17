from django.contrib import admin
from .models import Balance, Transaction, Account, AutoTopUp

admin.site.register(Balance)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(AutoTopUp)
