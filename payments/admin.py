# pylint: disable=missing-module-docstring,missing-class-docstring
from django.contrib import admin
from .models import (StripeTransaction, MemberTransaction,
                     OrganisationTransaction)

class MemberTransactionAdmin(admin.ModelAdmin):
    search_fields = ['reference_no', 'type']

class OrganisationTransactionAdmin(admin.ModelAdmin):
    search_fields = ['reference_no', 'type']

class StripeTransactionAdmin(admin.ModelAdmin):
    search_fields = ['stripe_reference']

admin.site.register(MemberTransaction, MemberTransactionAdmin)
admin.site.register(OrganisationTransaction, OrganisationTransactionAdmin)
admin.site.register(StripeTransaction, StripeTransactionAdmin)
