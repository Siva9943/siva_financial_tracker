"""Recurring transaction generation.

Deterministic and idempotent: calling this repeatedly (manually now, from a
Celery beat task from Phase 14 onward) never creates duplicate transactions
for the same rule + date.
"""

from dateutil.relativedelta import relativedelta
from django.db import transaction as db_transaction

from apps.transactions.models import RecurringTransaction, Transaction

_STEP = {
    RecurringTransaction.Frequency.DAILY: relativedelta(days=1),
    RecurringTransaction.Frequency.WEEKLY: relativedelta(weeks=1),
    RecurringTransaction.Frequency.MONTHLY: relativedelta(months=1),
    RecurringTransaction.Frequency.YEARLY: relativedelta(years=1),
}


def _generate_for_rule(rule, as_of):
    created = []
    run_date = rule.next_run_date

    while run_date <= as_of and (rule.end_date is None or run_date <= rule.end_date):
        _, was_created = Transaction.objects.get_or_create(
            recurring_transaction=rule,
            transaction_date=run_date,
            defaults={
                'user': rule.user,
                'transaction_type': rule.transaction_type,
                'amount': rule.amount,
                'category': rule.category,
                'description': rule.description,
                'payment_method': rule.payment_method,
            },
        )
        if was_created:
            created.append(run_date)
        run_date = run_date + _STEP[rule.frequency]

    rule.next_run_date = run_date
    if rule.end_date and rule.next_run_date > rule.end_date:
        rule.is_active = False
    rule.save(update_fields=['next_run_date', 'is_active'])

    return created


def generate_due_transactions(user, as_of=None):
    """Generate any Transaction rows due for the user's active recurring rules.

    Returns {rule_id: [dates generated]}.
    """
    from datetime import date

    as_of = as_of or date.today()
    results = {}

    with db_transaction.atomic():
        due_rules = RecurringTransaction.objects.select_for_update().filter(
            user=user, is_active=True, next_run_date__lte=as_of
        )
        for rule in due_rules:
            generated_dates = _generate_for_rule(rule, as_of)
            if generated_dates:
                results[rule.id] = generated_dates

    return results
