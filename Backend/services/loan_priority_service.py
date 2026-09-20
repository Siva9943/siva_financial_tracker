"""Deterministic loan payoff prioritization (skill §20).

Purely a ranking + explanation layer over existing Loan data — never
delegated to an LLM, and never mutates the loans it ranks.
"""

from .interest_service import InterestCalculationService
from .rounding import round_money

STRATEGIES = ('AVALANCHE', 'SNOWBALL', 'CUSTOM')


def _estimated_monthly_interest(loan):
    """A rough, method-agnostic monthly interest figure for comparing loans side by side."""
    return InterestCalculationService.monthly_interest(loan.outstanding_principal, loan.annual_interest_rate)


def _priority_level(rank, total):
    if total <= 1:
        return 'High'
    high_cutoff = -(-total // 3)  # ceil(total / 3)
    medium_cutoff = -(-2 * total // 3)  # ceil(2 * total / 3)
    if rank <= high_cutoff:
        return 'High'
    if rank <= medium_cutoff:
        return 'Medium'
    return 'Low'


def _sort_key(strategy):
    if strategy == 'AVALANCHE':
        return lambda loan: (-loan.annual_interest_rate, loan.id)
    if strategy == 'SNOWBALL':
        return lambda loan: (loan.outstanding_principal, loan.id)
    if strategy == 'CUSTOM':
        return lambda loan: (loan.priority_order is None, loan.priority_order or 0, loan.id)
    raise ValueError(f'Unknown loan priority strategy: {strategy}')


def _reason(strategy, loan, monthly_interest, rank):
    if strategy == 'AVALANCHE':
        return (
            f'{loan.annual_interest_rate}% annual interest rate\n'
            f'{monthly_interest} estimated monthly interest — the highest rate is paid off first.'
        )
    if strategy == 'SNOWBALL':
        return (
            f'{round_money(loan.outstanding_principal)} outstanding balance\n'
            f'Smallest remaining balance is paid off first to build momentum.'
        )
    if rank is not None and loan.priority_order is not None:
        return f'Manually prioritized by you (position {loan.priority_order}).'
    return 'No custom position set — ranked after all manually ordered loans.'


def rank_loans(loans, strategy='AVALANCHE'):
    """Rank an iterable of Loan instances (all belonging to one user).

    Returns a list of dicts, highest priority first, each with a rank,
    priority_level (High/Medium/Low), and a human-readable reason.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f'Unknown loan priority strategy: {strategy}')

    ordered = sorted(loans, key=_sort_key(strategy))
    total = len(ordered)

    results = []
    for rank, loan in enumerate(ordered, start=1):
        monthly_interest = _estimated_monthly_interest(loan)
        results.append(
            {
                'loan_id': loan.id,
                'loan_name': loan.loan_name,
                'rank': rank,
                'priority_level': _priority_level(rank, total),
                'annual_interest_rate': loan.annual_interest_rate,
                'outstanding_principal': loan.outstanding_principal,
                'estimated_monthly_interest': monthly_interest,
                'reason': _reason(strategy, loan, monthly_interest, rank),
            }
        )
    return results
