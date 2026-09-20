import django_filters

from .models import Investment, InvestmentTransaction


class InvestmentFilter(django_filters.FilterSet):
    class Meta:
        model = Investment
        fields = ('investment_type', 'status', 'platform')


class InvestmentTransactionFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='transaction_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='transaction_date', lookup_expr='lte')

    class Meta:
        model = InvestmentTransaction
        fields = ('transaction_type', 'date_from', 'date_to')
