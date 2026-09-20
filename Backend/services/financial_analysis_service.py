"""Financial ratio analytics (skill §25).

Reports current value, the previous period's value, and the raw change
between them for each ratio — deliberately not a single blended "financial
health score", which the skill explicitly rules out.
"""

from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum

from apps.analytics.date_ranges import month_end, month_start, resolve_range
from apps.loans.models import LoanPayment
from apps.transactions.models import Transaction

METRIC_KEYS = ('savings_rate', 'debt_to_income', 'expense_ratio', 'interest_burden')


def _percentage(numerator, denominator):
    if not denominator:
        return None
    return round(float(numerator) / float(denominator) * 100, 2)


def period_totals(user, start, end):
    income = Transaction.objects.filter(
        user=user, transaction_type=Transaction.TransactionType.INCOME, transaction_date__range=(start, end)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    expenses = Transaction.objects.filter(
        user=user, transaction_type=Transaction.TransactionType.EXPENSE, transaction_date__range=(start, end)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    payments = LoanPayment.objects.filter(loan__user=user, payment_date__range=(start, end)).aggregate(
        debt_payments=Sum('amount'), interest_paid=Sum('interest_component')
    )

    return {
        'income': income,
        'expenses': expenses,
        'debt_payments': payments['debt_payments'] or Decimal('0.00'),
        'interest_paid': payments['interest_paid'] or Decimal('0.00'),
    }


def calculate_ratios(totals):
    return {
        'savings_rate': _percentage(totals['income'] - totals['expenses'], totals['income']),
        'debt_to_income': _percentage(totals['debt_payments'], totals['income']),
        'expense_ratio': _percentage(totals['expenses'], totals['income']),
        'interest_burden': _percentage(totals['interest_paid'], totals['debt_payments']),
    }


def _historical_series(user, range_key, bounds, periods):
    series = []

    if range_key == 'CUSTOM':
        span_days = (bounds['end'] - bounds['start']).days + 1
        cursor_end = bounds['end']
        for _ in range(periods):
            cursor_start = cursor_end - timedelta(days=span_days - 1)
            ratios = calculate_ratios(period_totals(user, cursor_start, cursor_end))
            series.append({'label': f'{cursor_start.isoformat()} – {cursor_end.isoformat()}', **ratios})
            cursor_end = cursor_start - timedelta(days=1)

    elif range_key == 'CURRENT_YEAR':
        anchor = bounds['end']
        for i in range(periods):
            year = anchor.year - i
            s, e = (date(year, 1, 1), anchor) if year == anchor.year else (date(year, 1, 1), date(year, 12, 31))
            ratios = calculate_ratios(period_totals(user, s, e))
            series.append({'label': str(year), **ratios})

    else:  # CURRENT_MONTH / PREVIOUS_MONTH — monthly buckets
        anchor = bounds['end']
        for i in range(periods):
            month_date = anchor - relativedelta(months=i)
            s = month_start(month_date)
            e = anchor if i == 0 else month_end(month_date)
            ratios = calculate_ratios(period_totals(user, s, e))
            series.append({'label': s.strftime('%b %Y'), **ratios})

    series.reverse()
    return series


def get_financial_analytics(user, range_key, start=None, end=None, history_periods=6, today=None):
    bounds = resolve_range(range_key, start=start, end=end, today=today)

    current_totals = period_totals(user, bounds['start'], bounds['end'])
    previous_totals = period_totals(user, bounds['previous_start'], bounds['previous_end'])
    current_ratios = calculate_ratios(current_totals)
    previous_ratios = calculate_ratios(previous_totals)

    metrics = {}
    for key in METRIC_KEYS:
        current_value = current_ratios[key]
        previous_value = previous_ratios[key]
        change = round(current_value - previous_value, 2) if current_value is not None and previous_value is not None else None
        metrics[key] = {'current': current_value, 'previous': previous_value, 'change': change}

    return {
        'range': {'start': bounds['start'], 'end': bounds['end']},
        'previous_range': {'start': bounds['previous_start'], 'end': bounds['previous_end']},
        'metrics': metrics,
        'historical': _historical_series(user, range_key, bounds, history_periods),
        'totals': {**current_totals, 'savings': current_totals['income'] - current_totals['expenses']},
    }
