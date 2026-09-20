"""Repayment planner projection (skill §21).

Given a user's active monthly loans, a payoff strategy, and how much extra
they can pay each month, deterministically simulates the payoff month by
month: every loan gets its normal EMI, and all "extra" capacity (the stated
extra_payment plus any EMI freed up by loans that have already closed) goes
to whichever loan the strategy currently ranks first.

Pure function over plain data — the caller persists the result.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from apps.loans.date_utils import PERIODS_PER_YEAR, advance_date, count_periods
from apps.loans.schedule import compute_next_installment
from services.emi_service import EMICalculationService
from services.loan_priority_service import rank_loans
from services.rounding import round_money

MAX_MONTHS = 600  # 50 years — a safety valve, not an expected outcome


class RepaymentPlanError(Exception):
    """Raised for business-rule violations the caller should surface as a 400."""


@dataclass
class _LoanSnapshot:
    """A mutable, in-memory stand-in for a Loan during simulation — never persisted."""

    id: int
    loan_name: str
    outstanding_principal: Decimal
    annual_interest_rate: Decimal
    interest_calculation_method: str
    payment_frequency: str
    start_date: date
    maturity_date: date
    original_principal: Decimal
    emi_amount: Decimal
    priority_order: int | None
    last_date: date
    closed: bool = field(default=False)


def _build_snapshot(loan, as_of):
    emi_amount = loan.emi_amount
    if emi_amount is None:
        tenure_periods = count_periods(loan.start_date, loan.maturity_date, loan.payment_frequency)
        emi_amount = EMICalculationService.calculate_emi(
            loan.original_principal, loan.annual_interest_rate, tenure_periods, PERIODS_PER_YEAR[loan.payment_frequency]
        )

    return _LoanSnapshot(
        id=loan.id,
        loan_name=loan.loan_name,
        outstanding_principal=loan.outstanding_principal,
        annual_interest_rate=loan.annual_interest_rate,
        interest_calculation_method=loan.interest_calculation_method,
        payment_frequency=loan.payment_frequency,
        start_date=loan.start_date,
        maturity_date=loan.maturity_date,
        original_principal=loan.original_principal,
        emi_amount=emi_amount,
        priority_order=loan.priority_order,
        last_date=as_of,
    )


def generate_repayment_plan(
    loans, *, strategy, monthly_income, essential_expenses, emergency_savings_allocation, extra_payment, as_of=None
):
    as_of = as_of or date.today()
    monthly_income = Decimal(monthly_income)
    essential_expenses = Decimal(essential_expenses)
    emergency_savings_allocation = Decimal(emergency_savings_allocation)
    extra_payment = Decimal(extra_payment)

    eligible_loans = [loan for loan in loans if loan.payment_frequency == 'MONTHLY']
    excluded_loans = [
        {'loan_id': loan.id, 'loan_name': loan.loan_name, 'reason': 'Only monthly-frequency loans are included in this planner.'}
        for loan in loans
        if loan.payment_frequency != 'MONTHLY'
    ]

    if not eligible_loans:
        raise RepaymentPlanError('No active monthly loans are available to plan for.')

    snapshots = [_build_snapshot(loan, as_of) for loan in eligible_loans]
    total_existing_emi = round_money(sum((s.emi_amount for s in snapshots), Decimal('0.00')))

    available_capacity = round_money(
        monthly_income - essential_expenses - emergency_savings_allocation - total_existing_emi
    )
    if extra_payment > available_capacity:
        raise RepaymentPlanError(
            f'Extra payment of {round_money(extra_payment)} exceeds your available monthly capacity of '
            f'{available_capacity} after essential expenses, existing EMIs, and savings allocation.'
        )

    assumptions = [
        'All included loans are stepped monthly, regardless of their configured payment frequency.',
        'Each loan\'s normal EMI stays fixed for the life of the plan, as it would in a real amortization schedule.',
        'Extra payment capacity each month goes entirely to the single top-priority loan; any amount left over '
        'after that loan is fully paid off in its final month is not carried over to another loan that same month.',
        'When a loan is paid off, its EMI is added to the pool of extra payment capacity starting the following month.',
    ]
    if excluded_loans:
        assumptions.append('Loans with a non-monthly payment frequency were excluded from this plan.')

    by_id = {s.id: s for s in snapshots}
    items = []
    redirected_capacity = Decimal('0.00')
    month_date = as_of
    month_number = 0

    while any(not s.closed for s in snapshots):
        month_number += 1
        if month_number > MAX_MONTHS:
            raise RepaymentPlanError('Projection exceeded the maximum planning horizon (50 years) — check loan terms.')

        month_date = advance_date(month_date, 'MONTHLY')
        open_snapshots = [s for s in snapshots if not s.closed]
        total_extra_this_month = extra_payment + redirected_capacity

        ranked = rank_loans(open_snapshots, strategy)
        top_id = ranked[0]['loan_id']

        for snapshot in open_snapshots:
            installment = compute_next_installment(snapshot, accrual_start_date=snapshot.last_date, payment_date=month_date)
            interest_due = installment['interest']

            if snapshot.emi_amount <= interest_due:
                raise RepaymentPlanError(
                    f'The EMI for "{snapshot.loan_name}" does not cover its accruing interest and would never '
                    'pay it off. Increase the EMI or review the interest rate before planning.'
                )

            normal_principal = min(snapshot.emi_amount - interest_due, snapshot.outstanding_principal)

            extra_applied = Decimal('0.00')
            if snapshot.id == top_id:
                remaining_after_normal = snapshot.outstanding_principal - normal_principal
                extra_applied = min(total_extra_this_month, remaining_after_normal)

            principal_paid = round_money(normal_principal + extra_applied)
            closing_balance = round_money(snapshot.outstanding_principal - principal_paid)

            items.append(
                {
                    'month_number': month_number,
                    'month_date': month_date,
                    'loan_id': snapshot.id,
                    'loan_name': snapshot.loan_name,
                    'normal_emi': round_money(snapshot.emi_amount),
                    'extra_payment': round_money(extra_applied),
                    'principal_paid': principal_paid,
                    'interest_paid': interest_due,
                    'closing_balance': closing_balance,
                }
            )

            snapshot.outstanding_principal = closing_balance
            snapshot.last_date = month_date
            if closing_balance <= 0:
                snapshot.closed = True
                redirected_capacity += snapshot.emi_amount

    total_interest = round_money(sum((Decimal(item['interest_paid']) for item in items), Decimal('0.00')))
    total_payment = round_money(
        sum((Decimal(item['principal_paid']) + Decimal(item['interest_paid']) for item in items), Decimal('0.00'))
    )

    return {
        'items': items,
        'total_existing_emi': total_existing_emi,
        'available_capacity': available_capacity,
        'total_interest': total_interest,
        'total_payment': total_payment,
        'months_remaining': month_number,
        'expected_payoff_date': month_date,
        'assumptions': assumptions,
        'excluded_loans': excluded_loans,
    }
