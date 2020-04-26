from django.contrib import admin
from .models import Balance, StripeTransaction, InternalTransaction, AutoTopUpConfig

class InternalTransactionAdmin(admin.ModelAdmin):
    search_fields = ['reference_no', 'type']

class StripeTransactionAdmin(admin.ModelAdmin):
    search_fields = ['stripe_reference']

admin.site.register(Balance)
admin.site.register(InternalTransaction, InternalTransactionAdmin)
admin.site.register(StripeTransaction, StripeTransactionAdmin)
admin.site.register(AutoTopUpConfig)
