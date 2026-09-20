"""Scheduled background jobs for the investments module (skill §11-12).

Mirrors apps.notifications.tasks: every task here is idempotent, so running
it twice — or twice concurrently — must never produce inconsistent data.
"""

from datetime import date, timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.notifications.models import Notification
from apps.notifications.tasks import _notify_once
from services.portfolio_snapshot_service import create_or_update_snapshot

from .models import Investment

STALE_PRICE_DAYS = 30


@shared_task
def create_daily_portfolio_snapshot(snapshot_date=None):
    User = get_user_model()
    users = User.objects.filter(investments__isnull=False).distinct()
    for user in users:
        create_or_update_snapshot(user, snapshot_date)
    return users.count()


@shared_task
def remind_stale_investment_prices(today=None):
    """Once a month, nudge users to refresh current_price on holdings that haven't been
    updated in a while — current_price is manually maintained (skill §36), so without a
    reminder it silently goes stale and every P/L figure built on it drifts with it.

    Dedupe key includes the year-month, so this can run daily without spamming: each
    investment gets at most one stale-price notification per calendar month.
    """
    today = today or date.today()
    cutoff = today - timedelta(days=STALE_PRICE_DAYS)
    stale = Investment.objects.filter(status=Investment.Status.ACTIVE).filter(
        Q(current_price_updated_at__isnull=True) | Q(current_price_updated_at__date__lt=cutoff)
    )

    sent = 0
    for investment in stale.select_related('user'):
        created = _notify_once(
            investment.user,
            Notification.NotificationType.STALE_INVESTMENT_PRICE,
            title=f'Update the price for "{investment.name}"',
            message=f'"{investment.name}" hasn\'t had its current price updated in over {STALE_PRICE_DAYS} days — update it to keep your returns accurate.',
            dedupe_key=f'stale-investment-price:{investment.id}:{today.year}-{today.month:02d}',
        )
        sent += int(created)
    return sent
