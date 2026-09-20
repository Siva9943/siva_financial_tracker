from django.contrib import admin

from .models import Loan, LoanPayment


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'loan_name', 'loan_type', 'outstanding_principal', 'status', 'next_due_date')
    list_filter = ('loan_type', 'status', 'interest_calculation_method')
    search_fields = ('loan_name', 'lender', 'user__username')


@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'payment_date', 'amount', 'principal_component', 'interest_component', 'remaining_principal')
    list_filter = ('payment_date',)
    search_fields = ('loan__loan_name', 'transaction_reference')
