"""Daily portfolio snapshots (skill §11-12).

create_or_update_snapshot is the single source of truth for writing a
snapshot row, used by both the daily Celery task and the "create today's
snapshot immediately" call made right after a user's first investment
activity (see apps.investments.views) — a fresh account should never have
to wait a full day to see its first PortfolioPerformanceChart data point.

Idempotent by construction: update_or_create keyed on (user, snapshot_date)
recomputes and overwrites with the same deterministic figures every time,
backed by the DB's UniqueConstraint as the final guarantee against a race
between two concurrent runs.
"""

from datetime import date

from apps.investments.models import PortfolioSnapshot

from .investment_performance_service import get_portfolio_performance


def create_or_update_snapshot(user, snapshot_date=None):
    snapshot_date = snapshot_date or date.today()
    portfolio = get_portfolio_performance(user)

    snapshot, _ = PortfolioSnapshot.objects.update_or_create(
        user=user,
        snapshot_date=snapshot_date,
        defaults={
            'total_invested': portfolio['total_invested'],
            'portfolio_value': portfolio['current_value'],
            'profit_loss': portfolio['capital_gain'],
            'dividend_income': portfolio['dividend_income'],
        },
    )
    return snapshot
