from django.conf import settings
from django.db import models


class FinancialGoal(models.Model):
    class GoalType(models.TextChoices):
        EMERGENCY_FUND = 'EMERGENCY_FUND', 'Emergency Fund'
        EDUCATION = 'EDUCATION', 'Education'
        VEHICLE = 'VEHICLE', 'Vehicle'
        HOUSE = 'HOUSE', 'House'
        VACATION = 'VACATION', 'Vacation'
        CUSTOM = 'CUSTOM', 'Custom Goal'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        ABANDONED = 'ABANDONED', 'Abandoned'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=100)
    goal_type = models.CharField(max_length=20, choices=GoalType.choices)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_date = models.DateField()
    # The user's planned monthly savings toward this goal — used to project a completion date.
    monthly_contribution = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.IN_PROGRESS)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('target_date',)
        indexes = [models.Index(fields=('user', 'status'))]
        constraints = [
            models.CheckConstraint(condition=models.Q(target_amount__gt=0), name='goal_target_amount_positive'),
            models.CheckConstraint(condition=models.Q(current_amount__gte=0), name='goal_current_amount_non_negative'),
        ]

    def __str__(self):
        return f'{self.name} ({self.user_id})'


class GoalContribution(models.Model):
    goal = models.ForeignKey(FinancialGoal, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    contribution_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-contribution_date', '-created_at')
        indexes = [models.Index(fields=('goal', 'contribution_date'))]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='goal_contribution_amount_positive'),
        ]

    def __str__(self):
        return f'{self.amount} on {self.contribution_date} for goal {self.goal_id}'
