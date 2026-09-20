from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def default_alert_thresholds():
    return [50, 75, 90, 100]


class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.PositiveIntegerField()
    # Percentages (e.g. [50, 75, 90, 100]) at which a usage alert should fire. User-configurable.
    alert_thresholds = models.JSONField(default=default_alert_thresholds)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-year', '-month', 'category')
        indexes = [models.Index(fields=('user', 'month', 'year'))]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='budget_amount_positive'),
            models.UniqueConstraint(fields=('user', 'category', 'month', 'year'), name='unique_budget_per_category_month'),
        ]

    def __str__(self):
        return f'{self.category} budget for {self.month}/{self.year} ({self.user_id})'
