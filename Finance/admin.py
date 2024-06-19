from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(RawFeePayment)
admin.site.register(StudentFeePayment)
admin.site.register(TermFeeStructure)
admin.site.register(Invoices)
admin.site.register(InvoicePayments)
admin.site.register(FeeDebit)