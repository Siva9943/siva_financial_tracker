"""Dashboard aggregation (skill §26).

Pure orchestration — every actual calculation is delegated to the
already-tested aggregation function for that domain (transactions, loans,
budgets), so this module has nothing novel to get wrong on its own.
"""

from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate, TruncMonth

from apps.budgets.models import Budget
from apps.loans.models import Loan, LoanPayment
from apps.loans.aggregations import loan_summary
from apps.loans.schedule import build_schedule_response
from apps.transactions.aggregations import category_breakdown
from apps.transactions.models import Transaction
from services.budget_service import build_spent_lookup, calculate_budget_usage

ZERO = Decimal('0.00')


def _bucketed_totals(queryset, trunc_fn):
    rows = (
        queryset.annotate(bucket=trunc_fn('transaction_date'))
        .values('bucket')
        .annotate(total=Sum('amount'))
        .order_by('bucket')
    )
    return {row['bucket']: row['total'] for row in rows}


def _income_vs_expense_series(income_qs, expense_qs, start, end):
    span_days = (end - start).days + 1
    trunc_fn = TruncDate if span_days <= 31 else TruncMonth

    income_by_bucket = _bucketed_totals(income_qs, trunc_fn)
    expense_by_bucket = _bucketed_totals(expense_qs, trunc_fn)

    buckets = sorted(set(income_by_bucket) | set(expense_by_bucket))
    series = []
    for bucket in buckets:
        income = income_by_bucket.get(bucket, ZERO)
        expense = expense_by_bucket.get(bucket, ZERO)
        series.append({'period': bucket, 'income': income, 'expense': expense, 'savings': income - expense})
    return series


def _months_spanned(start, end):
    months = set()
    cursor = start.replace(day=1)
    while cursor <= end:
        months.add((cursor.month, cursor.year))
        cursor = cursor + relativedelta(months=1)
    return months


def _budget_usage_summary(user, start, end):
    months = _months_spanned(start, end)
    if not months:
        return {'total_budgeted': ZERO, 'total_spent': ZERO, 'categories': []}

    condition = Q()
    for month, year in months:
        condition |= Q(month=month, year=year)
    budgets = Budget.objects.filter(user=user).filter(condition)

    if not budgets.exists():
        return {'total_budgeted': ZERO, 'total_spent': ZERO, 'categories': []}

    lookup = build_spent_lookup(user, budgets)
    total_budgeted = ZERO
    total_spent = ZERO
    categories = []

    for budget in budgets:
        spent = lookup.get((budget.category, budget.month, budget.year), ZERO)
        usage = calculate_budget_usage(budget.amount, spent, budget.alert_thresholds)
        total_budgeted += budget.amount
        total_spent += usage['spent']
        categories.append({'category': budget.category, 'month': budget.month, 'year': budget.year, 'amount': budget.amount, **usage})

    return {'total_budgeted': total_budgeted, 'total_spent': total_spent, 'categories': categories}


def _debt_payoff_projection(loans, months=12, today=None):
    """Total combined outstanding balance for the next `months`, if nothing changes.

    Only MONTHLY-frequency loans are included — matches the same simplifying
    assumption the repayment planner makes, so the month index lines up.
    """
    today = today or date.today()
    totals = [ZERO] * months

    for loan in loans:
        if loan.payment_frequency != Loan.PaymentFrequency.MONTHLY:
            continue
        try:
            result = build_schedule_response(
                principal=loan.outstanding_principal,
                annual_rate=loan.annual_interest_rate,
                method=loan.interest_calculation_method,
                frequency=loan.payment_frequency,
                start_date=today,
                maturity_date=loan.maturity_date,
                emi=loan.emi_amount,
            )
        except ValueError:
            continue

        schedule = result['schedule']
        for i in range(months):
            totals[i] += schedule[i]['closing_balance'] if i < len(schedule) else ZERO

    return [{'month': i + 1, 'total_outstanding': totals[i]} for i in range(months)]


def build_dashboard(user, start, end):
    income_qs = Transaction.objects.filter(user=user, transaction_type=Transaction.TransactionType.INCOME, transaction_date__range=(start, end))
    expense_qs = Transaction.objects.filter(user=user, transaction_type=Transaction.TransactionType.EXPENSE, transaction_date__range=(start, end))

    total_income = income_qs.aggregate(total=Sum('amount'))['total'] or ZERO
    total_expenses = expense_qs.aggregate(total=Sum('amount'))['total'] or ZERO
    savings = total_income - total_expenses

    loans = Loan.objects.filter(user=user, status__in=(Loan.Status.ACTIVE, Loan.Status.OVERDUE))
    loan_totals = loans.aggregate(total_debt=Sum('original_principal'), outstanding=Sum('outstanding_principal'))
    summary = loan_summary(loans)

    payments_qs = LoanPayment.objects.filter(loan__user=user, payment_date__range=(start, end))
    payment_totals = payments_qs.aggregate(interest=Sum('interest_component'), principal=Sum('principal_component'), amount=Sum('amount'))
    interest_paid = payment_totals['interest'] or ZERO
    principal_paid = payment_totals['principal'] or ZERO
    debt_payments_this_period = payment_totals['amount'] or ZERO

    cards = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'savings': savings,
        'total_debt': loan_totals['total_debt'] or ZERO,
        'outstanding_principal': loan_totals['outstanding'] or ZERO,
        'interest_paid': interest_paid,
        'monthly_emi': summary['monthly_debt_payment'],
        'available_balance': savings - debt_payments_this_period,
    }

    charts = {
        'income_vs_expense': _income_vs_expense_series(income_qs, expense_qs, start, end),
        'expense_by_category': category_breakdown(expense_qs),
        'loan_balance': [
            {'loan_name': loan.loan_name, 'outstanding_principal': loan.outstanding_principal} for loan in loans
        ],
        'interest_vs_principal': {'interest': interest_paid, 'principal': principal_paid},
        'budget_usage': _budget_usage_summary(user, start, end),
        'debt_payoff_projection': _debt_payoff_projection(loans),
    }

    return {'cards': cards, 'charts': charts}
