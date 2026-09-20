from django.conf import settings
from django.db import models


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'Income'
        EXPENSE = 'EXPENSE', 'Expense'
        LOAN_PAYMENT = 'LOAN_PAYMENT', 'Loan Payment'
        REFUND = 'REFUND', 'Refund'
        TRANSFER = 'TRANSFER', 'Transfer'

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        UPI = 'UPI', 'UPI'
        CARD = 'CARD', 'Card'
        CHEQUE = 'CHEQUE', 'Cheque'
        OTHER = 'OTHER', 'Other'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    transaction_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.OTHER)
    reference = models.CharField(max_length=100, blank=True)
    recurring_transaction = models.ForeignKey(
        'RecurringTransaction', null=True, blank=True, on_delete=models.SET_NULL, related_name='generated_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-transaction_date', '-created_at')
        indexes = [
            models.Index(fields=('user', 'transaction_date')),
            models.Index(fields=('user', 'transaction_type')),
            models.Index(fields=('user', 'category')),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='transaction_amount_positive'),
        ]

    def __str__(self):
        return f'{self.transaction_type} {self.amount} on {self.transaction_date} ({self.user_id})'


class RecurringTransaction(models.Model):
    """A template that periodically generates real Transaction records.

    Generation itself is idempotent (see services.transaction_service) so it
    can be triggered manually here or later from a Celery beat task without
    creating duplicates.
    """

    class Frequency(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'
        YEARLY = 'YEARLY', 'Yearly'

    RECURRING_TYPES = (
        (Transaction.TransactionType.INCOME, 'Income'),
        (Transaction.TransactionType.EXPENSE, 'Expense'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=RECURRING_TYPES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    payment_method = models.CharField(
        max_length=20, choices=Transaction.PaymentMethod.choices, default=Transaction.PaymentMethod.OTHER
    )
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    start_date = models.DateField()
    next_run_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('next_run_date',)
        indexes = [models.Index(fields=('user', 'is_active', 'next_run_date'))]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='recurring_amount_positive'),
        ]

    def __str__(self):
        return f'{self.transaction_type} {self.amount} every {self.frequency} ({self.user_id})'
