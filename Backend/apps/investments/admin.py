from django.contrib import admin

from .models import Investment, InvestmentTransaction, PortfolioSnapshot


class InvestmentTransactionInline(admin.TabularInline):
    model = InvestmentTransaction
    extra = 0


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'investment_type', 'quantity', 'total_invested', 'current_price', 'status')
    list_filter = ('investment_type', 'status')
    search_fields = ('name', 'symbol', 'user__username')
    inlines = [InvestmentTransactionInline]


@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'investment', 'transaction_type', 'transaction_date', 'quantity', 'price', 'amount')
    list_filter = ('transaction_type',)
    search_fields = ('investment__name', 'user__username', 'reference')


@admin.register(PortfolioSnapshot)
class PortfolioSnapshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'snapshot_date', 'total_invested', 'portfolio_value', 'profit_loss')
    list_filter = ('snapshot_date',)
    search_fields = ('user__username',)
