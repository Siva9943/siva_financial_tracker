import django_filters

from .models import FinancialGoal


class FinancialGoalFilter(django_filters.FilterSet):
    class Meta:
        model = FinancialGoal
        fields = ('goal_type', 'priority', 'status')
