"""Database-side aggregation helpers for income/expense summaries.

Keeps totals and breakdowns computed in PostgreSQL rather than pulled into
Python/React row-by-row (skill requirement: aggregate in the DB).
"""

from datetime import date, timedelta

from django.db.models import Sum
from django.db.models.functions import TruncMonth


def _period_bounds(today):
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)
    return {
        'today': (today, today),
        'this_week': (start_of_week, today),
        'this_month': (start_of_month, today),
        'this_year': (start_of_year, today),
    }


def period_totals(queryset, today=None):
    today = today or date.today()
    totals = {}
    for label, (start, end) in _period_bounds(today).items():
        total = queryset.filter(transaction_date__gte=start, transaction_date__lte=end).aggregate(
            total=Sum('amount')
        )['total']
        totals[label] = total or 0
    return totals


def category_breakdown(queryset, date_from=None, date_to=None):
    if date_from:
        queryset = queryset.filter(transaction_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(transaction_date__lte=date_to)

    rows = list(
        queryset.values('category').annotate(total=Sum('amount')).order_by('-total')
    )
    grand_total = sum((row['total'] for row in rows), 0)

    for row in rows:
        row['percentage'] = round(float(row['total']) / float(grand_total) * 100, 2) if grand_total else 0

    return rows


def _add_months(anchor, delta):
    month_index = anchor.month - 1 + delta
    year = anchor.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def monthly_trend(queryset, months=6, today=None):
    """Zero-filled month-by-month totals for the trailing `months` months."""
    today = today or date.today()
    earliest_month = _add_months(today.replace(day=1), -(months - 1))

    rows = (
        queryset.filter(transaction_date__gte=earliest_month)
        .annotate(month=TruncMonth('transaction_date'))
        .values('month')
        .annotate(total=Sum('amount'))
    )
    totals_by_month = {row['month'].strftime('%Y-%m'): row['total'] or 0 for row in rows}

    return [
        {'month': key, 'total': totals_by_month.get(key, 0)}
        for key in (_add_months(earliest_month, i).strftime('%Y-%m') for i in range(months))
    ]


def monthly_trend_by_type(queryset, months=6, today=None):
    """Zero-filled month-by-month income/expense totals for the trailing `months` months."""
    today = today or date.today()
    earliest_month = _add_months(today.replace(day=1), -(months - 1))

    rows = (
        queryset.filter(transaction_date__gte=earliest_month)
        .annotate(month=TruncMonth('transaction_date'))
        .values('month', 'transaction_type')
        .annotate(total=Sum('amount'))
    )
    by_month = {}
    for row in rows:
        key = row['month'].strftime('%Y-%m')
        entry = by_month.setdefault(key, {'income': 0, 'expense': 0})
        field = 'income' if row['transaction_type'] == 'INCOME' else 'expense'
        entry[field] = row['total'] or 0

    return [
        {'month': key, **by_month.get(key, {'income': 0, 'expense': 0})}
        for key in (_add_months(earliest_month, i).strftime('%Y-%m') for i in range(months))
    ]
