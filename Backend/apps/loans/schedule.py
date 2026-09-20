"""Glue between Loan-shaped parameters and the EMI/interest calculation services."""

from decimal import Decimal

from services.emi_service import EMICalculationService
from services.interest_service import InterestCalculationService
from services.rounding import round_money

from .date_utils import PERIODS_PER_YEAR, count_periods


def build_schedule_response(*, principal, annual_rate, method, frequency, start_date, maturity_date, emi=None, extra_payment=Decimal('0.00')):
    tenure_periods = count_periods(start_date, maturity_date, frequency)
    if tenure_periods <= 0:
        raise ValueError('Loan term must span at least one full payment period.')

    periods_per_year = PERIODS_PER_YEAR[frequency]

    calculated_emi = None
    if method in ('EMI_AMORTIZATION', 'MONTHLY_REDUCING_BALANCE') and emi is None:
        effective_periods_per_year = 12 if method == 'MONTHLY_REDUCING_BALANCE' else periods_per_year
        calculated_emi = EMICalculationService.calculate_emi(principal, annual_rate, tenure_periods, effective_periods_per_year)

    schedule = EMICalculationService.generate_schedule(
        principal=principal,
        annual_rate=annual_rate,
        tenure_periods=tenure_periods,
        periods_per_year=periods_per_year,
        start_date=start_date,
        frequency=frequency,
        method=method,
        emi=emi or calculated_emi,
        extra_payment=extra_payment,
    )

    total_payment = sum((row['payment'] for row in schedule), Decimal('0.00'))
    total_interest = sum((row['interest'] for row in schedule), Decimal('0.00'))

    return {
        'tenure_periods': tenure_periods,
        'months_to_payoff': len(schedule),
        'payoff_date': schedule[-1]['date'],
        'emi': calculated_emi or emi,
        'total_principal': Decimal(principal),
        'total_interest': total_interest,
        'total_payment': total_payment,
        'schedule': schedule,
    }


def compare_extra_payment_scenarios(
    *, principal, annual_rate, method, frequency, start_date, maturity_date, emi=None, extra_payments
):
    """What-if comparison (skill §22): baseline (no extra payment) vs. each requested extra-payment amount."""
    baseline = build_schedule_response(
        principal=principal, annual_rate=annual_rate, method=method, frequency=frequency,
        start_date=start_date, maturity_date=maturity_date, emi=emi, extra_payment=Decimal('0.00'),
    )

    scenarios = []
    for extra in extra_payments:
        result = build_schedule_response(
            principal=principal, annual_rate=annual_rate, method=method, frequency=frequency,
            start_date=start_date, maturity_date=maturity_date, emi=emi, extra_payment=extra,
        )
        scenarios.append(
            {
                'extra_payment': extra,
                'emi': result['emi'],
                'months_to_payoff': result['months_to_payoff'],
                'payoff_date': result['payoff_date'],
                'total_interest': result['total_interest'],
                'total_payment': result['total_payment'],
                'months_saved': baseline['months_to_payoff'] - result['months_to_payoff'],
                'interest_saved': baseline['total_interest'] - result['total_interest'],
            }
        )

    return {
        'baseline': {
            'emi': baseline['emi'],
            'months_to_payoff': baseline['months_to_payoff'],
            'payoff_date': baseline['payoff_date'],
            'total_interest': baseline['total_interest'],
            'total_payment': baseline['total_payment'],
        },
        'scenarios': scenarios,
    }


def compute_next_installment(loan, *, accrual_start_date, payment_date):
    """The interest/principal split the loan's own terms expect for its next payment.

    Computed from the loan's *current* outstanding_principal (so extra payments
    already made correctly shrink future interest), while interest accrual for
    FLAT_RATE and the scheduled principal slice always reference the loan's
    original terms, since those never change with early payment.
    """
    method = loan.interest_calculation_method
    original_tenure_periods = count_periods(loan.start_date, loan.maturity_date, loan.payment_frequency)
    periods_per_year = PERIODS_PER_YEAR[loan.payment_frequency]

    if method == 'FLAT_RATE':
        tenure_years = Decimal(original_tenure_periods) / Decimal(periods_per_year)
        total_interest = InterestCalculationService.flat_rate_total_interest(
            loan.original_principal, loan.annual_interest_rate, tenure_years
        )
        interest = round_money(total_interest / original_tenure_periods)
        scheduled_principal = round_money(loan.original_principal / original_tenure_periods)
        return {'interest': interest, 'scheduled_principal': scheduled_principal}

    if method == 'DAILY_REDUCING_BALANCE':
        days_elapsed = (payment_date - accrual_start_date).days
        interest = InterestCalculationService.interest_for_days(
            loan.outstanding_principal, loan.annual_interest_rate, max(days_elapsed, 0)
        )
        scheduled_principal = round_money(loan.original_principal / original_tenure_periods)
        return {'interest': interest, 'scheduled_principal': scheduled_principal}

    # EMI_AMORTIZATION / MONTHLY_REDUCING_BALANCE: standard reducing-balance math.
    effective_periods_per_year = 12 if method == 'MONTHLY_REDUCING_BALANCE' else periods_per_year
    periodic_rate = InterestCalculationService.periodic_rate(loan.annual_interest_rate, effective_periods_per_year)
    interest = round_money(loan.outstanding_principal * periodic_rate) if periodic_rate else Decimal('0.00')

    emi = loan.emi_amount or EMICalculationService.calculate_emi(
        loan.original_principal, loan.annual_interest_rate, original_tenure_periods, effective_periods_per_year
    )
    scheduled_principal = emi - interest
    return {'interest': interest, 'scheduled_principal': scheduled_principal}
