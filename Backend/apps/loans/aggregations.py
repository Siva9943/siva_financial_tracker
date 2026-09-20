"""Loan summary aggregation.

Interest-paid / remaining-interest / total-amount-paid figures depend on the
calculation engine (Phase 7) and payment history (Phase 8), which don't exist
yet — this summary only reports what the Loan model itself can answer today.
"""

from django.db.models import Sum

from .models import Loan


def loan_summary(queryset):
    active = queryset.filter(status=Loan.Status.ACTIVE)

    totals = queryset.aggregate(
        total_original_principal=Sum('original_principal'),
        total_outstanding_principal=Sum('outstanding_principal'),
    )
    monthly_debt_payment = active.filter(payment_frequency=Loan.PaymentFrequency.MONTHLY).aggregate(
        total=Sum('emi_amount')
    )['total']

    next_due = active.exclude(next_due_date__isnull=True).order_by('next_due_date').values_list('next_due_date', flat=True).first()

    return {
        'total_original_principal': totals['total_original_principal'] or 0,
        'total_outstanding_principal': totals['total_outstanding_principal'] or 0,
        'active_loan_count': active.count(),
        'completed_loan_count': queryset.filter(status=Loan.Status.COMPLETED).count(),
        'monthly_debt_payment': monthly_debt_payment or 0,
        'next_due_date': next_due,
    }
