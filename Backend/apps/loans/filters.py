import django_filters

from .models import Loan


class LoanFilter(django_filters.FilterSet):
    class Meta:
        model = Loan
        fields = ('loan_type', 'status', 'interest_calculation_method')
