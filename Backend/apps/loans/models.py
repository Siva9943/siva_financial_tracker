from django.conf import settings
from django.db import models

from .date_utils import advance_date


class Loan(models.Model):
    class LoanType(models.TextChoices):
        PERSONAL = 'PERSONAL', 'Personal'
        HOME = 'HOME', 'Home'
        VEHICLE = 'VEHICLE', 'Vehicle'
        EDUCATION = 'EDUCATION', 'Education'
        CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
        BUSINESS = 'BUSINESS', 'Business'
        GOLD_LOAN = 'GOLD_LOAN', 'Gold Loan'
        OTHER = 'OTHER', 'Other'

    class InterestMethod(models.TextChoices):
        DAILY_REDUCING_BALANCE = 'DAILY_REDUCING_BALANCE', 'Daily Reducing Balance'
        MONTHLY_REDUCING_BALANCE = 'MONTHLY_REDUCING_BALANCE', 'Monthly Reducing Balance'
        EMI_AMORTIZATION = 'EMI_AMORTIZATION', 'EMI Amortization'
        FLAT_RATE = 'FLAT_RATE', 'Flat Rate'

    class PaymentFrequency(models.TextChoices):
        WEEKLY = 'WEEKLY', 'Weekly'
        BIWEEKLY = 'BIWEEKLY', 'Biweekly'
        MONTHLY = 'MONTHLY', 'Monthly'
        QUARTERLY = 'QUARTERLY', 'Quarterly'
        YEARLY = 'YEARLY', 'Yearly'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        OVERDUE = 'OVERDUE', 'Overdue'
        PAUSED = 'PAUSED', 'Paused'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')
    loan_name = models.CharField(max_length=100)
    loan_type = models.CharField(max_length=20, choices=LoanType.choices)
    lender = models.CharField(max_length=100, blank=True)

    original_principal = models.DecimalField(max_digits=14, decimal_places=2)
    outstanding_principal = models.DecimalField(max_digits=14, decimal_places=2)
    annual_interest_rate = models.DecimalField(max_digits=6, decimal_places=3)
    interest_calculation_method = models.CharField(max_length=30, choices=InterestMethod.choices)

    emi_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    payment_frequency = models.CharField(max_length=10, choices=PaymentFrequency.choices, default=PaymentFrequency.MONTHLY)

    start_date = models.DateField()
    maturity_date = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)

    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Percentage of outstanding principal charged on early payoff, e.g. 2.00 = 2%.
    prepayment_penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    # User-defined payoff order for the CUSTOM priority strategy; 1 = highest priority.
    priority_order = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('user', 'status')),
            models.Index(fields=('user', 'next_due_date')),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(original_principal__gt=0), name='loan_original_principal_positive'),
            models.CheckConstraint(condition=models.Q(outstanding_principal__gte=0), name='loan_outstanding_principal_non_negative'),
            models.CheckConstraint(condition=models.Q(annual_interest_rate__gte=0), name='loan_interest_rate_non_negative'),
            models.CheckConstraint(condition=models.Q(maturity_date__gt=models.F('start_date')), name='loan_maturity_after_start'),
        ]

    def __str__(self):
        return f'{self.loan_name} ({self.user_id})'

    def save(self, *args, **kwargs):
        # Only default these on creation — a later update setting next_due_date
        # to None (loan payoff) must not be silently re-filled here.
        if self.pk is None:
            if self.outstanding_principal is None:
                self.outstanding_principal = self.original_principal
            if self.next_due_date is None:
                self.next_due_date = advance_date(self.start_date, self.payment_frequency)
        super().save(*args, **kwargs)


class LoanPayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    principal_component = models.DecimalField(max_digits=14, decimal_places=2)
    interest_component = models.DecimalField(max_digits=14, decimal_places=2)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Portion of principal_component beyond what the schedule expected this period — informational only.
    extra_payment = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    remaining_principal = models.DecimalField(max_digits=14, decimal_places=2)
    transaction = models.ForeignKey(
        'transactions.Transaction', null=True, blank=True, on_delete=models.SET_NULL, related_name='loan_payments'
    )
    transaction_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-payment_date', '-created_at')
        indexes = [models.Index(fields=('loan', 'payment_date'))]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='loan_payment_amount_positive'),
        ]

    def __str__(self):
        return f'{self.amount} on {self.payment_date} for loan {self.loan_id}'
