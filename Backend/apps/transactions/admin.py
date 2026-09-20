from django.contrib import admin

from .models import RecurringTransaction, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'category', 'transaction_date')
    list_filter = ('transaction_type', 'category', 'payment_method')
    search_fields = ('description', 'reference', 'category', 'user__username')


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'frequency', 'next_run_date', 'is_active')
    list_filter = ('transaction_type', 'frequency', 'is_active')
    search_fields = ('category', 'description', 'user__username')
