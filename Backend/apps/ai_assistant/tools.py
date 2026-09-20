"""Deterministic backend tools the AI assistant may call (skill §30).

Every tool here is bound to one authenticated `user` via closure when
`build_financial_tools(user)` is called — the LLM never supplies or can
override whose data it reads, and every tool only reads; none of them can
create, modify, or execute anything. All figures come straight from the
same services and querysets the rest of the app uses — nothing is
recalculated or invented here.
"""

import json
from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from langchain_core.tools import tool

from apps.budgets.models import Budget
from apps.loans.models import Loan
from apps.loans.schedule import compare_extra_payment_scenarios
from apps.transactions.aggregations import category_breakdown
from apps.transactions.models import Transaction
from services.budget_service import build_spent_lookup, calculate_budget_usage


def _to_json(payload):
    return json.dumps(payload, default=str)


def _month_bounds(month, year):
    today = date.today()
    month = month or today.month
    year = year or today.year
    start = date(year, month, 1)
    end = start + relativedelta(months=1) - timedelta(days=1)
    return month, year, start, end


def build_financial_tools(user):
    @tool
    def get_monthly_income(month: int = None, year: int = None) -> str:
        """Get the user's total recorded income for a given month and year.

        If month/year are omitted, uses the current month.
        """
        month, year, start, end = _month_bounds(month, year)
        total = Transaction.objects.filter(
            user=user, transaction_type=Transaction.TransactionType.INCOME, transaction_date__range=(start, end)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return _to_json({'month': month, 'year': year, 'total_income': total})

    @tool
    def get_monthly_expenses(month: int = None, year: int = None) -> str:
        """Get the user's total recorded expenses for a given month and year.

        If month/year are omitted, uses the current month.
        """
        month, year, start, end = _month_bounds(month, year)
        total = Transaction.objects.filter(
            user=user, transaction_type=Transaction.TransactionType.EXPENSE, transaction_date__range=(start, end)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return _to_json({'month': month, 'year': year, 'total_expenses': total})

    @tool
    def get_expense_by_category(month: int = None, year: int = None) -> str:
        """Get a breakdown of the user's expenses by category for a given month and year.

        If month/year are omitted, uses the current month.
        """
        month, year, start, end = _month_bounds(month, year)
        queryset = Transaction.objects.filter(
            user=user, transaction_type=Transaction.TransactionType.EXPENSE, transaction_date__range=(start, end)
        )
        return _to_json({'month': month, 'year': year, 'breakdown': category_breakdown(queryset)})

    @tool
    def get_active_loans() -> str:
        """List the user's active and overdue loans with their key figures."""
        loans = Loan.objects.filter(user=user, status__in=(Loan.Status.ACTIVE, Loan.Status.OVERDUE))
        return _to_json(
            [
                {
                    'loan_name': loan.loan_name,
                    'loan_type': loan.loan_type,
                    'outstanding_principal': loan.outstanding_principal,
                    'annual_interest_rate': loan.annual_interest_rate,
                    'emi_amount': loan.emi_amount,
                    'next_due_date': loan.next_due_date,
                    'status': loan.status,
                }
                for loan in loans
            ]
        )

    @tool
    def get_loan_details(loan_name: str) -> str:
        """Get full details for one of the user's loans by its name (case-insensitive, partial match ok)."""
        loan = Loan.objects.filter(user=user, loan_name__icontains=loan_name).first()
        if loan is None:
            return _to_json({'error': f'No loan found matching "{loan_name}".'})
        return _to_json(
            {
                'loan_name': loan.loan_name,
                'loan_type': loan.loan_type,
                'lender': loan.lender,
                'original_principal': loan.original_principal,
                'outstanding_principal': loan.outstanding_principal,
                'annual_interest_rate': loan.annual_interest_rate,
                'interest_calculation_method': loan.interest_calculation_method,
                'emi_amount': loan.emi_amount,
                'payment_frequency': loan.payment_frequency,
                'start_date': loan.start_date,
                'maturity_date': loan.maturity_date,
                'next_due_date': loan.next_due_date,
                'status': loan.status,
            }
        )

    @tool
    def calculate_loan_scenario(loan_name: str, extra_payment: float) -> str:
        """Calculate the effect of paying a fixed extra amount each period on one of the user's loans.

        Returns the baseline (no extra payment) and the requested scenario side by side,
        including months saved and interest saved.
        """
        loan = Loan.objects.filter(user=user, loan_name__icontains=loan_name).first()
        if loan is None:
            return _to_json({'error': f'No loan found matching "{loan_name}".'})
        if loan.maturity_date <= date.today():
            return _to_json({'error': f'"{loan.loan_name}" has already reached its maturity date.'})

        result = compare_extra_payment_scenarios(
            principal=loan.outstanding_principal,
            annual_rate=loan.annual_interest_rate,
            method=loan.interest_calculation_method,
            frequency=loan.payment_frequency,
            start_date=date.today(),
            maturity_date=loan.maturity_date,
            emi=loan.emi_amount,
            extra_payments=[Decimal(str(extra_payment))],
        )
        return _to_json({'loan_name': loan.loan_name, **result})

    @tool
    def get_upcoming_payments(days: int = 30) -> str:
        """List the user's loan payments due within the next N days (default 30)."""
        today = date.today()
        loans = Loan.objects.filter(
            user=user, status=Loan.Status.ACTIVE, next_due_date__isnull=False,
            next_due_date__range=(today, today + timedelta(days=days)),
        ).order_by('next_due_date')
        return _to_json(
            [
                {'loan_name': loan.loan_name, 'due_date': loan.next_due_date, 'emi_amount': loan.emi_amount}
                for loan in loans
            ]
        )

    @tool
    def get_budget_status(month: int = None, year: int = None) -> str:
        """Get the user's budget usage by category for a given month and year.

        If month/year are omitted, uses the current month.
        """
        month, year, _, _ = _month_bounds(month, year)
        budgets = list(Budget.objects.filter(user=user, month=month, year=year))
        if not budgets:
            return _to_json({'month': month, 'year': year, 'budgets': []})

        lookup = build_spent_lookup(user, budgets)
        budgets_out = []
        for budget in budgets:
            spent = lookup.get((budget.category, budget.month, budget.year), Decimal('0.00'))
            usage = calculate_budget_usage(budget.amount, spent, budget.alert_thresholds)
            budgets_out.append({'category': budget.category, 'amount': budget.amount, **usage})

        return _to_json({'month': month, 'year': year, 'budgets': budgets_out})

    return [
        get_monthly_income,
        get_monthly_expenses,
        get_expense_by_category,
        get_active_loans,
        get_loan_details,
        calculate_loan_scenario,
        get_upcoming_payments,
        get_budget_status,
    ]
