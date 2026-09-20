from django.contrib import admin

from .models import FinancialGoal, GoalContribution


class GoalContributionInline(admin.TabularInline):
    model = GoalContribution
    extra = 0


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'goal_type', 'current_amount', 'target_amount', 'status')
    list_filter = ('goal_type', 'priority', 'status')
    search_fields = ('name', 'user__username')
    inlines = [GoalContributionInline]
