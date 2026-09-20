"""EMI calculation and amortization schedule generation (skill §17-18, §22).

Pure Decimal math, no persistence, no ORM access. Given a loan's own
parameters it produces the same schedule shape regardless of interest
method, so callers (the loan-calculator API, the per-loan amortization
endpoint, the payment workflow, and the what-if simulator) don't need
method-specific branching of their own.

Every schedule generator accepts an optional `extra_payment` — an amount
added to the normal per-period principal payment. It defaults to 0, in
which case behavior is identical to a plain schedule. A non-zero extra
payment can only shorten the payoff (never lengthen it), so the original
`tenure_periods` remains a safe iteration upper bound in every case.
"""

from decimal import Decimal

from apps.loans.date_utils import advance_date

from .interest_service import InterestCalculationService
from .rounding import round_money

ONE = Decimal('1')
ZERO = Decimal('0.00')


class EMICalculationService:
    @staticmethod
    def calculate_emi(principal, annual_rate, tenure_periods, periods_per_year):
        """EMI = P x r x (1+r)^n / ((1+r)^n - 1); falls back to simple division at 0% interest."""
        principal = Decimal(principal)
        if tenure_periods <= 0:
            raise ValueError('tenure_periods must be greater than zero.')

        periodic_rate = InterestCalculationService.periodic_rate(annual_rate, periods_per_year)

        if periodic_rate == 0:
            return round_money(principal / tenure_periods)

        growth = (ONE + periodic_rate) ** tenure_periods
        emi = principal * periodic_rate * growth / (growth - ONE)
        return round_money(emi)

    @staticmethod
    def _reducing_balance_schedule(
        principal, annual_rate, tenure_periods, periods_per_year, start_date, frequency, emi=None, extra_payment=ZERO
    ):
        principal = Decimal(principal)
        extra_payment = Decimal(extra_payment)
        periodic_rate = InterestCalculationService.periodic_rate(annual_rate, periods_per_year)
        emi = Decimal(emi) if emi is not None else EMICalculationService.calculate_emi(
            principal, annual_rate, tenure_periods, periods_per_year
        )

        schedule = []
        balance = principal
        period_date = start_date

        for period in range(1, tenure_periods + 1):
            period_date = advance_date(period_date, frequency)
            interest = round_money(balance * periodic_rate) if periodic_rate else Decimal('0.00')
            principal_component = emi - interest + extra_payment

            is_last_period = period == tenure_periods or principal_component >= balance
            if is_last_period:
                principal_component = balance
                payment = round_money(principal_component + interest)
                closing_balance = Decimal('0.00')
            else:
                payment = round_money(emi + extra_payment)
                closing_balance = round_money(balance - principal_component)

            schedule.append(
                {
                    'period': period,
                    'date': period_date,
                    'opening_balance': round_money(balance),
                    'payment': payment,
                    'principal': round_money(principal_component),
                    'interest': interest,
                    'closing_balance': closing_balance,
                }
            )

            balance = closing_balance
            if is_last_period:
                break

        return schedule

    @staticmethod
    def _flat_rate_schedule(principal, annual_rate, tenure_periods, periods_per_year, start_date, frequency, extra_payment=ZERO):
        principal = Decimal(principal)
        extra_payment = Decimal(extra_payment)
        tenure_years = Decimal(tenure_periods) / Decimal(periods_per_year)
        total_interest = InterestCalculationService.flat_rate_total_interest(principal, annual_rate, tenure_years)

        principal_component = round_money(principal / tenure_periods)
        interest_component = round_money(total_interest / tenure_periods)

        schedule = []
        balance = principal
        period_date = start_date

        for period in range(1, tenure_periods + 1):
            period_date = advance_date(period_date, frequency)
            this_principal = principal_component + extra_payment

            is_last_period = period == tenure_periods or this_principal >= balance
            if is_last_period:
                this_principal = round_money(balance)
                closing_balance = Decimal('0.00')
            else:
                this_principal = round_money(this_principal)
                closing_balance = round_money(balance - this_principal)

            schedule.append(
                {
                    'period': period,
                    'date': period_date,
                    'opening_balance': round_money(balance),
                    'payment': round_money(this_principal + interest_component),
                    'principal': this_principal,
                    'interest': interest_component,
                    'closing_balance': closing_balance,
                }
            )
            balance = closing_balance
            if is_last_period:
                break

        return schedule

    @staticmethod
    def _daily_reducing_balance_schedule(
        principal, annual_rate, tenure_periods, start_date, frequency, day_count_basis=365, extra_payment=ZERO
    ):
        principal = Decimal(principal)
        extra_payment = Decimal(extra_payment)
        schedule = []
        balance = principal
        period_start = start_date

        for period in range(1, tenure_periods + 1):
            period_end = advance_date(period_start, frequency)
            days_in_period = (period_end - period_start).days

            interest = InterestCalculationService.interest_for_days(balance, annual_rate, days_in_period, day_count_basis)
            principal_component = round_money(principal / tenure_periods) + extra_payment

            is_last_period = period == tenure_periods or principal_component >= balance
            if is_last_period:
                principal_component = round_money(balance)
                closing_balance = Decimal('0.00')
            else:
                principal_component = round_money(principal_component)
                closing_balance = round_money(balance - principal_component)

            schedule.append(
                {
                    'period': period,
                    'date': period_end,
                    'opening_balance': round_money(balance),
                    'payment': round_money(principal_component + interest),
                    'principal': principal_component,
                    'interest': interest,
                    'closing_balance': closing_balance,
                }
            )

            balance = closing_balance
            period_start = period_end
            if is_last_period:
                break

        return schedule

    @staticmethod
    def generate_schedule(
        *,
        principal,
        annual_rate,
        tenure_periods,
        periods_per_year,
        start_date,
        frequency,
        method,
        emi=None,
        day_count_basis=365,
        extra_payment=ZERO,
    ):
        if method in ('EMI_AMORTIZATION', 'MONTHLY_REDUCING_BALANCE'):
            effective_periods_per_year = 12 if method == 'MONTHLY_REDUCING_BALANCE' else periods_per_year
            return EMICalculationService._reducing_balance_schedule(
                principal, annual_rate, tenure_periods, effective_periods_per_year, start_date, frequency,
                emi=emi, extra_payment=extra_payment,
            )
        if method == 'FLAT_RATE':
            return EMICalculationService._flat_rate_schedule(
                principal, annual_rate, tenure_periods, periods_per_year, start_date, frequency, extra_payment=extra_payment
            )
        if method == 'DAILY_REDUCING_BALANCE':
            return EMICalculationService._daily_reducing_balance_schedule(
                principal, annual_rate, tenure_periods, start_date, frequency, day_count_basis, extra_payment=extra_payment
            )
        raise ValueError(f'Unknown interest calculation method: {method}')
