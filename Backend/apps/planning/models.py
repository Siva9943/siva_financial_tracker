from django.conf import settings
from django.db import models


class RepaymentPlan(models.Model):
    class Strategy(models.TextChoices):
        AVALANCHE = 'AVALANCHE', 'Avalanche'
        SNOWBALL = 'SNOWBALL', 'Snowball'
        CUSTOM = 'CUSTOM', 'Custom'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='repayment_plans')
    strategy = models.CharField(max_length=10, choices=Strategy.choices)

    monthly_income = models.DecimalField(max_digits=14, decimal_places=2)
    essential_expenses = models.DecimalField(max_digits=14, decimal_places=2)
    emergency_savings_allocation = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    extra_payment = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_existing_emi = models.DecimalField(max_digits=14, decimal_places=2)

    months_remaining = models.PositiveIntegerField()
    expected_payoff_date = models.DateField()
    total_interest = models.DecimalField(max_digits=14, decimal_places=2)
    total_payment = models.DecimalField(max_digits=14, decimal_places=2)

    # Human-readable notes on simplifications made during generation (skill: "make all assumptions visible").
    assumptions = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('user', '-created_at'))]

    def __str__(self):
        return f'{self.strategy} plan for {self.user_id} ({self.created_at:%Y-%m-%d})'


class PlanItem(models.Model):
    plan = models.ForeignKey(RepaymentPlan, on_delete=models.CASCADE, related_name='items')
    month_number = models.PositiveIntegerField()
    month_date = models.DateField()
    loan = models.ForeignKey('loans.Loan', null=True, on_delete=models.SET_NULL, related_name='plan_items')
    # Preserved even if the loan is later deleted, matching how InterestRecord-style history should behave.
    loan_name = models.CharField(max_length=100)

    normal_emi = models.DecimalField(max_digits=14, decimal_places=2)
    extra_payment = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    principal_paid = models.DecimalField(max_digits=14, decimal_places=2)
    interest_paid = models.DecimalField(max_digits=14, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ('month_number', 'loan_name')
        indexes = [models.Index(fields=('plan', 'month_number'))]

    def __str__(self):
        return f'Month {self.month_number} — {self.loan_name}'
