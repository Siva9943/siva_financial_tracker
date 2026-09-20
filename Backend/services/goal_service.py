"""Financial goal progress and contribution recording (skill §27).

Progress figures are computed fresh from the goal's current state — nothing
here is persisted or cached, so there is nothing that can go stale.
"""

from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import transaction as db_transaction

from apps.goals.models import FinancialGoal

from .rounding import round_money


class GoalContributionError(Exception):
    """Raised for business-rule violations the caller should surface as a 400."""


def _months_between(start, end):
    if end <= start:
        return 0
    delta = relativedelta(end, start)
    months = delta.years * 12 + delta.months
    if delta.days > 0:
        months += 1
    return max(months, 1)


def calculate_goal_progress(goal, today=None):
    today = today or date.today()

    remaining_amount = round_money(max(goal.target_amount - goal.current_amount, Decimal('0.00')))
    percentage_complete = round(float(goal.current_amount) / float(goal.target_amount) * 100, 2) if goal.target_amount else 0.0

    months_to_target = _months_between(today, goal.target_date)
    required_monthly_contribution = (
        Decimal('0.00') if remaining_amount <= 0 else round_money(remaining_amount / months_to_target)
    )

    estimated_completion_date = None
    if remaining_amount <= 0:
        estimated_completion_date = today
    elif goal.monthly_contribution > 0:
        months_needed = -(-remaining_amount // goal.monthly_contribution)  # ceiling division
        estimated_completion_date = today + relativedelta(months=int(months_needed))

    return {
        'remaining_amount': remaining_amount,
        'percentage_complete': percentage_complete,
        'required_monthly_contribution': required_monthly_contribution,
        'estimated_completion_date': estimated_completion_date,
        'is_on_track': (
            estimated_completion_date is not None
            and goal.target_date is not None
            and estimated_completion_date <= goal.target_date
        ),
    }


def record_contribution(goal, *, amount, contribution_date, notes=''):
    amount = round_money(amount)
    if amount <= 0:
        raise GoalContributionError('Contribution amount must be greater than zero.')
    if goal.status != FinancialGoal.Status.IN_PROGRESS:
        raise GoalContributionError(f'Cannot contribute to a goal with status {goal.status}.')

    with db_transaction.atomic():
        contribution = goal.contributions.create(amount=amount, contribution_date=contribution_date, notes=notes)
        goal.current_amount = round_money(goal.current_amount + amount)
        if goal.current_amount >= goal.target_amount:
            goal.status = FinancialGoal.Status.COMPLETED
        goal.save(update_fields=['current_amount', 'status', 'updated_at'])

    return contribution
