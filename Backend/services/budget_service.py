"""Budget usage and threshold-alert calculation (skill §23-24).

Pure computation over an amount/spent pair — no persistence. The alert
thresholds a budget crosses are computed fresh on every read rather than
stored, so there is nothing here that could go stale or duplicate; Phase 14
reuses this exact function when it starts persisting actual Notification
records on a schedule.
"""

from decimal import Decimal

from django.db.models import Sum

from apps.transactions.models import Transaction

from .rounding import round_money


def get_spent_for_budget(budget):
    total = Transaction.objects.filter(
        user_id=budget.user_id,
        transaction_type=Transaction.TransactionType.EXPENSE,
        category=budget.category,
        transaction_date__year=budget.year,
        transaction_date__month=budget.month,
    ).aggregate(total=Sum('amount'))['total']
    return total or Decimal('0.00')


def build_spent_lookup(user, budgets):
    """One aggregate query per distinct (month, year) among `budgets`, not one per budget."""
    periods = {(b.month, b.year) for b in budgets}
    lookup = {}

    for month, year in periods:
        rows = Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__year=year,
            transaction_date__month=month,
        ).values('category').annotate(total=Sum('amount'))
        for row in rows:
            lookup[(row['category'], month, year)] = row['total']

    return lookup


def calculate_budget_usage(amount, spent, alert_thresholds):
    amount = Decimal(amount)
    spent = Decimal(spent or 0)

    percentage_used = round(float(spent) / float(amount) * 100, 2) if amount else 0.0
    remaining = round_money(amount - spent)
    crossed_thresholds = sorted(t for t in alert_thresholds if percentage_used >= t)

    if percentage_used >= 100:
        status = 'EXCEEDED'
    elif crossed_thresholds:
        status = 'APPROACHING'
    else:
        status = 'OK'

    return {
        'spent': round_money(spent),
        'remaining': remaining,
        'percentage_used': percentage_used,
        'status': status,
        'crossed_thresholds': crossed_thresholds,
    }
