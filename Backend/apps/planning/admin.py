from django.contrib import admin

from .models import PlanItem, RepaymentPlan


class PlanItemInline(admin.TabularInline):
    model = PlanItem
    extra = 0


@admin.register(RepaymentPlan)
class RepaymentPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'strategy', 'months_remaining', 'expected_payoff_date', 'total_interest', 'created_at')
    list_filter = ('strategy',)
    inlines = [PlanItemInline]
