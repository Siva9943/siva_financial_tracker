"""Interest calculation primitives (skill §13-16).

Pure Decimal math, no persistence, no ORM access — deterministic and
independently testable. Consumed by emi_service to build full amortization
schedules, and later by the loan-payment workflow (Phase 8) to price a
single payment.
"""

from decimal import Decimal

from .rounding import round_money

HUNDRED = Decimal('100')


class InterestCalculationService:
    @staticmethod
    def daily_interest(outstanding_principal, annual_rate, day_count_basis=365):
        """Daily Interest = Outstanding Principal x Annual Rate / Day Count Basis."""
        return round_money(Decimal(outstanding_principal) * Decimal(annual_rate) / HUNDRED / Decimal(day_count_basis))

    @staticmethod
    def interest_for_days(outstanding_principal, annual_rate, days, day_count_basis=365):
        """Interest accrued over an arbitrary number of days (e.g. a payment period)."""
        return round_money(
            Decimal(outstanding_principal) * Decimal(annual_rate) / HUNDRED / Decimal(day_count_basis) * Decimal(days)
        )

    @staticmethod
    def monthly_interest(outstanding_principal, annual_rate):
        """Interest for one month under monthly reducing balance."""
        return round_money(Decimal(outstanding_principal) * Decimal(annual_rate) / HUNDRED / Decimal(12))

    @staticmethod
    def periodic_rate(annual_rate, periods_per_year):
        """The per-period interest rate, e.g. monthly rate = annual_rate / 100 / 12."""
        return Decimal(annual_rate) / HUNDRED / Decimal(periods_per_year)

    @staticmethod
    def flat_rate_total_interest(principal, annual_rate, tenure_years):
        """Total interest for a flat-rate loan, charged on the original principal for the full tenure."""
        return round_money(Decimal(principal) * Decimal(annual_rate) / HUNDRED * Decimal(tenure_years))
