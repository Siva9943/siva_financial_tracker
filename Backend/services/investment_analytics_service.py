"""Day/week/month/year investment analytics (skill §9, §13, §18-19).

Two independent kinds of number are returned side by side, deliberately not
conflated:
- "live" portfolio figures (total_invested, current_value, profit_loss,
  return_percentage) — always the CURRENT state, delegated to
  investment_performance_service so there is one formula for them.
- "period" figures (contribution, dividend_income) — scoped to the
  requested date window, computed directly from InvestmentTransaction
  history, which is always fully reconstructable for any historical range.

get_contribution_trend() zero-fills every bucket in its lookback window
using the same discipline as apps.transactions.aggregations.monthly_trend —
a month/week/day with no transactions must show 0, never be omitted.
"""

from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek, TruncYear

from apps.investments.models import InvestmentTransaction

from .investment_performance_service import get_portfolio_performance
from .rounding import round_money

ZERO = Decimal('0.00')
PERIODS = ('day', 'week', 'month', 'year')

_CONTRIBUTION_TYPES = (InvestmentTransaction.TransactionType.BUY, InvestmentTransaction.TransactionType.DEPOSIT)

_TRUNC_FN = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth, 'year': TruncYear}
_LOOKBACK = {'day': 30, 'week': 12, 'month': 12, 'year': 5}
_LABEL_FMT = {'day': '%Y-%m-%d', 'week': '%Y-%m-%d', 'month': '%Y-%m', 'year': '%Y'}


class InvestmentAnalyticsError(Exception):
    """Raised for business-rule violations the caller should surface as a 400."""


def _require_valid_period(period):
    if period not in PERIODS:
        raise InvestmentAnalyticsError(f'Unknown period "{period}". Choose one of {", ".join(PERIODS)}.')


def _period_bounds(period, today):
    if period == 'day':
        return today, today
    if period == 'week':
        return today - timedelta(days=today.weekday()), today
    if period == 'month':
        return today.replace(day=1), today
    return today.replace(month=1, day=1), today


def get_investment_analytics(user, period, today=None):
    """A single snapshot: current portfolio state + this period's contribution/dividends."""
    _require_valid_period(period)
    today = today or date.today()
    start, end = _period_bounds(period, today)

    period_qs = InvestmentTransaction.objects.filter(user=user, transaction_date__range=(start, end))
    contribution = round_money(
        period_qs.filter(transaction_type__in=_CONTRIBUTION_TYPES).aggregate(total=Sum('amount'))['total'] or ZERO
    )
    dividend_income = round_money(
        period_qs.filter(transaction_type=InvestmentTransaction.TransactionType.DIVIDEND).aggregate(total=Sum('amount'))['total'] or ZERO
    )

    portfolio = get_portfolio_performance(user)

    return {
        'period': period,
        'range': {'start': start, 'end': end},
        'total_invested': portfolio['total_invested'],
        'current_value': portfolio['current_value'],
        'profit_loss': portfolio['capital_gain'],
        'return_percentage': portfolio['return_percentage'],
        'dividend_income': dividend_income,
        'contribution': contribution,
    }


def _earliest_bucket_start(period, today, count):
    if period == 'day':
        return today - timedelta(days=count - 1)
    if period == 'week':
        this_week_monday = today - timedelta(days=today.weekday())
        return this_week_monday - timedelta(weeks=count - 1)
    if period == 'month':
        return today.replace(day=1) - relativedelta(months=count - 1)
    return today.replace(month=1, day=1) - relativedelta(years=count - 1)


def _step_bucket(period, anchor, i):
    if period == 'day':
        return anchor + timedelta(days=i)
    if period == 'week':
        return anchor + timedelta(weeks=i)
    if period == 'month':
        return anchor + relativedelta(months=i)
    return anchor + relativedelta(years=i)


def get_contribution_trend(user, period, today=None, count=None):
    """Zero-filled contribution series, bucketed by `period`, for its default lookback window."""
    _require_valid_period(period)
    today = today or date.today()
    count = count or _LOOKBACK[period]
    earliest = _earliest_bucket_start(period, today, count)

    rows = (
        InvestmentTransaction.objects.filter(user=user, transaction_date__gte=earliest, transaction_type__in=_CONTRIBUTION_TYPES)
        .annotate(bucket=_TRUNC_FN[period]('transaction_date'))
        .values('bucket')
        .annotate(total=Sum('amount'))
    )
    fmt = _LABEL_FMT[period]
    totals_by_bucket = {row['bucket'].strftime(fmt): row['total'] or ZERO for row in rows}

    return [
        {'period': key, 'contribution': round_money(totals_by_bucket.get(key, ZERO))}
        for key in (_step_bucket(period, earliest, i).strftime(fmt) for i in range(count))
    ]
