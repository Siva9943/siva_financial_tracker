from django.conf import settings
from django.db import models


class Reminder(models.Model):
    class ReminderType(models.TextChoices):
        LOAN_EMI = 'LOAN_EMI', 'Loan EMI'
        CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
        INSURANCE = 'INSURANCE', 'Insurance'
        RENT = 'RENT', 'Rent'
        ELECTRICITY = 'ELECTRICITY', 'Electricity'
        RECURRING_EXPENSE = 'RECURRING_EXPENSE', 'Recurring Expense'
        FINANCIAL_GOAL = 'FINANCIAL_GOAL', 'Financial Goal'
        CUSTOM = 'CUSTOM', 'Custom'

    class Recurrence(models.TextChoices):
        NONE = 'NONE', 'None'
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'
        YEARLY = 'YEARLY', 'Yearly'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=ReminderType.choices)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    reminder_date = models.DateField()
    recurrence = models.CharField(max_length=10, choices=Recurrence.choices, default=Recurrence.NONE)
    is_completed = models.BooleanField(default=False)
    snoozed_until = models.DateField(null=True, blank=True)
    # Set by the Celery task once a Notification has gone out for the current reminder_date.
    last_notified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('reminder_date',)
        indexes = [models.Index(fields=('user', 'is_completed', 'reminder_date'))]

    def __str__(self):
        return f'{self.description} on {self.reminder_date} ({self.user_id})'


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        EMI_REMINDER = 'EMI_REMINDER', 'EMI Reminder'
        LOAN_OVERDUE = 'LOAN_OVERDUE', 'Loan Overdue'
        BUDGET_ALERT = 'BUDGET_ALERT', 'Budget Alert'
        RECURRING_TRANSACTION = 'RECURRING_TRANSACTION', 'Recurring Transaction'
        MONTHLY_SUMMARY = 'MONTHLY_SUMMARY', 'Monthly Summary'
        CUSTOM_REMINDER = 'CUSTOM_REMINDER', 'Custom Reminder'
        STALE_INVESTMENT_PRICE = 'STALE_INVESTMENT_PRICE', 'Stale Investment Price'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=25, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    # Identifies exactly what event this notification is about (e.g. "loan-overdue:12:2026-09-01"),
    # so a Celery task run twice — or run concurrently — can never create a duplicate.
    dedupe_key = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('user', 'is_read', '-created_at'))]
        constraints = [
            models.UniqueConstraint(fields=('user', 'dedupe_key'), name='unique_notification_per_user_event'),
        ]

    def __str__(self):
        return f'{self.title} ({self.user_id})'
