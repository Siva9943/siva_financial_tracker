"""Report data builders (skill §47).

Every builder returns the same shape — {title, generated_at, sections: [...]}
— so a single generic exporter (report_export.py) can render any of them to
CSV, Excel, or PDF. Every figure is pulled from the same aggregation
functions already used and tested elsewhere; nothing is recalculated here.
"""

from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from apps.analytics.dashboard import build_dashboard
from apps.budgets.models import Budget
from apps.investments.models import Investment, InvestmentTransaction
from apps.loans.aggregations import loan_summary
from apps.loans.models import Loan
from apps.planning.models import RepaymentPlan
from apps.transactions.aggregations import category_breakdown
from apps.transactions.models import Transaction
from services.budget_service import build_spent_lookup, calculate_budget_usage
from services.financial_analysis_service import calculate_ratios, period_totals
from services.investment_performance_service import get_portfolio_performance
from services.portfolio_service import allocation_by_type, build_holdings


class ReportError(Exception):
    """Raised when a report cannot be built (e.g. no data to report on)."""


def _summary_section(rows):
    return {'heading': 'Summary', 'columns': ['Metric', 'Value'], 'rows': rows}


def _financial_summary_report(user, title, start, end):
    totals = period_totals(user, start, end)
    ratios = calculate_ratios(totals)
    dashboard = build_dashboard(user, start, end)

    sections = [
        _summary_section(
            [
                ['Total Income', totals['income']],
                ['Total Expenses', totals['expenses']],
                ['Savings', totals['income'] - totals['expenses']],
                ['Savings Rate', f"{ratios['savings_rate']}%" if ratios['savings_rate'] is not None else '—'],
                ['Debt-to-Income', f"{ratios['debt_to_income']}%" if ratios['debt_to_income'] is not None else '—'],
                ['Expense Ratio', f"{ratios['expense_ratio']}%" if ratios['expense_ratio'] is not None else '—'],
                ['Interest Burden', f"{ratios['interest_burden']}%" if ratios['interest_burden'] is not None else '—'],
            ]
        ),
        {
            'heading': 'Income vs Expense',
            'columns': ['Period', 'Income', 'Expense', 'Savings'],
            'rows': [[row['period'], row['income'], row['expense'], row['savings']] for row in dashboard['charts']['income_vs_expense']],
        },
        {
            'heading': 'Expense by Category',
            'columns': ['Category', 'Total', 'Percentage'],
            'rows': [[row['category'], row['total'], f"{row['percentage']}%"] for row in dashboard['charts']['expense_by_category']],
        },
        {
            'heading': 'Loan Balance',
            'columns': ['Loan', 'Outstanding Principal'],
            'rows': [[row['loan_name'], row['outstanding_principal']] for row in dashboard['charts']['loan_balance']],
        },
    ]

    return {'title': title, 'generated_at': date.today(), 'sections': sections}


def build_monthly_report(user, month=None, year=None):
    today = date.today()
    month, year = month or today.month, year or today.year
    start = date(year, month, 1)
    end = start + relativedelta(months=1) - timedelta(days=1)
    return _financial_summary_report(user, f'Monthly Financial Report — {start.strftime("%B %Y")}', start, end)


def build_yearly_report(user, year=None):
    year = year or date.today().year
    start, end = date(year, 1, 1), date(year, 12, 31)
    return _financial_summary_report(user, f'Yearly Financial Report — {year}', start, end)


def build_loan_report(user):
    all_loans = list(Loan.objects.filter(user=user))
    active_loans = [loan for loan in all_loans if loan.status in (Loan.Status.ACTIVE, Loan.Status.OVERDUE)]
    summary = loan_summary(Loan.objects.filter(user=user, id__in=[loan.id for loan in active_loans]) if active_loans else Loan.objects.none())

    sections = [
        _summary_section(
            [
                ['Total Original Principal', summary['total_original_principal']],
                ['Total Outstanding Principal', summary['total_outstanding_principal']],
                ['Active Loan Count', summary['active_loan_count']],
                ['Completed Loan Count', summary['completed_loan_count']],
                ['Monthly Debt Payment', summary['monthly_debt_payment']],
                ['Next Due Date', summary['next_due_date'] or '—'],
            ]
        ),
        {
            'heading': 'Loans',
            'columns': ['Name', 'Type', 'Lender', 'Original Principal', 'Outstanding', 'Rate', 'EMI', 'Status', 'Next Due'],
            'rows': [
                [
                    loan.loan_name, loan.loan_type, loan.lender, loan.original_principal, loan.outstanding_principal,
                    f'{loan.annual_interest_rate}%', loan.emi_amount or '—', loan.status, loan.next_due_date or '—',
                ]
                for loan in all_loans
            ],
        },
    ]
    return {'title': 'Loan Report', 'generated_at': date.today(), 'sections': sections}


def build_expense_report(user, start, end):
    transactions = Transaction.objects.filter(
        user=user, transaction_type=Transaction.TransactionType.EXPENSE, transaction_date__range=(start, end)
    ).order_by('transaction_date')
    breakdown = category_breakdown(transactions)

    sections = [
        {
            'heading': 'Category Breakdown',
            'columns': ['Category', 'Total', 'Percentage'],
            'rows': [[row['category'], row['total'], f"{row['percentage']}%"] for row in breakdown],
        },
        {
            'heading': 'Transactions',
            'columns': ['Date', 'Category', 'Description', 'Amount', 'Payment Method'],
            'rows': [
                [txn.transaction_date, txn.category, txn.description or '—', txn.amount, txn.payment_method]
                for txn in transactions
            ],
        },
    ]
    return {'title': f'Expense Report — {start} to {end}', 'generated_at': date.today(), 'sections': sections}


def build_budget_report(user, month=None, year=None):
    today = date.today()
    month, year = month or today.month, year or today.year
    budgets = list(Budget.objects.filter(user=user, month=month, year=year))
    lookup = build_spent_lookup(user, budgets)

    rows = []
    for budget in budgets:
        spent = lookup.get((budget.category, budget.month, budget.year))
        usage = calculate_budget_usage(budget.amount, spent, budget.alert_thresholds)
        rows.append([budget.category, budget.amount, usage['spent'], usage['remaining'], f"{usage['percentage_used']}%", usage['status']])

    sections = [{'heading': 'Budgets', 'columns': ['Category', 'Budgeted', 'Spent', 'Remaining', '% Used', 'Status'], 'rows': rows}]
    return {'title': f'Budget Report — {month}/{year}', 'generated_at': date.today(), 'sections': sections}


def build_repayment_report(user, plan_id=None):
    queryset = RepaymentPlan.objects.filter(user=user)
    plan = queryset.filter(id=plan_id).first() if plan_id else queryset.order_by('-created_at').first()
    if plan is None:
        raise ReportError('No repayment plan found. Generate one from the Repayment Planner first.')

    sections = [
        _summary_section(
            [
                ['Strategy', plan.strategy],
                ['Months Remaining', plan.months_remaining],
                ['Expected Payoff Date', plan.expected_payoff_date],
                ['Total Interest', plan.total_interest],
                ['Total Payment', plan.total_payment],
            ]
        ),
        {
            'heading': 'Plan Items',
            'columns': ['Month', 'Date', 'Loan', 'Normal EMI', 'Extra', 'Principal', 'Interest', 'Closing Balance'],
            'rows': [
                [item.month_number, item.month_date, item.loan_name, item.normal_emi, item.extra_payment, item.principal_paid, item.interest_paid, item.closing_balance]
                for item in plan.items.all()
            ],
        },
    ]
    return {'title': f'Repayment Report — {plan.strategy.title()} Plan', 'generated_at': date.today(), 'sections': sections}


def build_investment_report(user):
    holdings = build_holdings(Investment.objects.filter(user=user))
    portfolio = get_portfolio_performance(user)

    sections = [
        _summary_section(
            [
                ['Total Invested', portfolio['total_invested']],
                ['Current Value', portfolio['current_value']],
                ['Total Return', portfolio['total_return']],
                ['Return %', f"{portfolio['return_percentage']}%"],
                ['Dividend Income', portfolio['dividend_income']],
                ['Number of Investments', portfolio['investment_count']],
            ]
        ),
        {
            'heading': 'Holdings',
            'columns': ['Investment', 'Type', 'Quantity', 'Avg Buy Price', 'Current Price', 'Invested', 'Current Value', 'Profit/Loss', 'Return %', 'Status'],
            'rows': [
                [
                    holding['name'], holding['investment_type'], holding['quantity'], holding['average_buy_price'],
                    holding['current_price'], holding['total_invested'], holding['current_value'],
                    holding['total_return'], f"{holding['return_percentage']}%", holding['status'],
                ]
                for holding in holdings
            ],
        },
    ]
    return {'title': 'Investment Report', 'generated_at': date.today(), 'sections': sections}


def build_portfolio_performance_report(user):
    portfolio = get_portfolio_performance(user)
    allocation = allocation_by_type(build_holdings(Investment.objects.filter(user=user)))

    sections = [
        _summary_section(
            [
                ['Total Invested', portfolio['total_invested']],
                ['Current Value', portfolio['current_value']],
                ['Realized Profit/Loss', portfolio['realized_profit_loss']],
                ['Unrealized Profit/Loss', portfolio['unrealized_profit_loss']],
                ['Capital Gain', portfolio['capital_gain']],
                ['Dividend Income', portfolio['dividend_income']],
                ['Fees', portfolio['total_fees']],
                ['Taxes', portfolio['total_tax']],
                ['Total Return', portfolio['total_return']],
                ['Return %', f"{portfolio['return_percentage']}%"],
                ['Methodology', portfolio['methodology']],
            ]
        ),
        {
            'heading': 'Allocation by Type',
            'columns': ['Type', 'Current Value', 'Percentage'],
            'rows': [[row['label'], row['current_value'], f"{row['percentage']}%"] for row in allocation],
        },
    ]
    return {'title': 'Portfolio Performance Report', 'generated_at': date.today(), 'sections': sections}


def build_dividend_report(user, start=None, end=None):
    dividends = InvestmentTransaction.objects.filter(user=user, transaction_type=InvestmentTransaction.TransactionType.DIVIDEND)
    if start:
        dividends = dividends.filter(transaction_date__gte=start)
    if end:
        dividends = dividends.filter(transaction_date__lte=end)
    dividends = dividends.select_related('investment').order_by('transaction_date')

    total = sum((row.amount for row in dividends), start=Decimal('0.00'))
    sections = [
        _summary_section([['Total Dividend Income', total], ['Number of Payouts', dividends.count()]]),
        {
            'heading': 'Dividend Payouts',
            'columns': ['Date', 'Investment', 'Amount', 'Reference', 'Notes'],
            'rows': [
                [row.transaction_date, row.investment.name, row.amount, row.reference or '—', row.notes or '—']
                for row in dividends
            ],
        },
    ]
    return {'title': 'Dividend Report', 'generated_at': date.today(), 'sections': sections}


def build_investment_transaction_report(user, start, end):
    transactions = InvestmentTransaction.objects.filter(
        user=user, transaction_date__range=(start, end)
    ).select_related('investment').order_by('transaction_date')

    sections = [
        {
            'heading': 'Investment Transactions',
            'columns': ['Date', 'Investment', 'Type', 'Quantity', 'Price', 'Amount', 'Fees', 'Tax', 'Reference'],
            'rows': [
                [
                    txn.transaction_date, txn.investment.name, txn.transaction_type, txn.quantity, txn.price,
                    txn.amount, txn.fees, txn.tax, txn.reference or '—',
                ]
                for txn in transactions
            ],
        },
    ]
    return {'title': f'Investment Transaction Report — {start} to {end}', 'generated_at': date.today(), 'sections': sections}
