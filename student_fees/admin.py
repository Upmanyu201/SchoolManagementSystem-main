from django.contrib import admin
from .models import FeeDeposit

@admin.register(FeeDeposit)
class FeeDepositAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'student', 'amount', 'paid_amount', 'deposit_date')
    list_filter = ('payment_mode', 'deposit_date')
    search_fields = ('receipt_no', 'student__admission_number', 'student__first_name')
    date_hierarchy = 'deposit_date'