"""Scheduled background jobs (skill §29).

Every task here is idempotent: it either checks for an existing record
before creating one, or relies on Notification's (user, dedupe_key) unique
constraint to make a duplicate run a no-op rather than a duplicate row.
Running any of these twice — or twice concurrently — must never create
double notifications or double financial records.
"""

from datetime import date, timedelta

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction as db_transaction
from django.utils import timezone

from apps.budgets.models import Budget
from apps.loans.models import Loan
from services.budget_service import calculate_budget_usage, get_spent_for_budget
from services.financial_analysis_service import get_financial_analytics
from services.transaction_service import generate_due_transactions

from .models import Notification, Reminder

EMI_REMINDER_LEAD_DAYS = 3

_RECURRENCE_STEP = {
    Reminder.Recurrence.DAILY: relativedelta(days=1),
    Reminder.Recurrence.WEEKLY: relativedelta(weeks=1),
    Reminder.Recurrence.MONTHLY: relativedelta(months=1),
    Reminder.Recurrence.YEARLY: relativedelta(years=1),
}


def _notify_once(user, notification_type, title, message, dedupe_key):
    """Create a Notification unless one with this exact dedupe_key already exists for this user.

    Relies on the DB unique constraint as the final word — a race between two
    concurrent task runs still can't produce two rows for the same event.
    """
    try:
        with db_transaction.atomic():
            _, created = Notification.objects.get_or_create(
                user=user,
                dedupe_key=dedupe_key,
                defaults={'notification_type': notification_type, 'title': title, 'message': message},
            )
        return created
    except IntegrityError:
        return False


@shared_task
def send_emi_reminders(today=None):
    today = today or date.today()
    horizon = today + timedelta(days=EMI_REMINDER_LEAD_DAYS)

    loans = Loan.objects.filter(status=Loan.Status.ACTIVE, next_due_date__isnull=False, next_due_date__range=(today, horizon))
    sent = 0
    for loan in loans:
        created = _notify_once(
            loan.user,
            Notification.NotificationType.EMI_REMINDER,
            title=f'Upcoming EMI for {loan.loan_name}',
            message=f'An EMI of {loan.emi_amount or "—"} for "{loan.loan_name}" is due on {loan.next_due_date}.',
            dedupe_key=f'emi-reminder:{loan.id}:{loan.next_due_date}',
        )
        sent += int(created)
    return sent


@shared_task
def detect_overdue_loans(today=None):
    today = today or date.today()
    loans = Loan.objects.filter(status=Loan.Status.ACTIVE, next_due_date__isnull=False, next_due_date__lt=today)
    flagged = 0
    for loan in loans:
        loan.status = Loan.Status.OVERDUE
        loan.save(update_fields=['status', 'updated_at'])
        created = _notify_once(
            loan.user,
            Notification.NotificationType.LOAN_OVERDUE,
            title=f'"{loan.loan_name}" is overdue',
            message=f'"{loan.loan_name}" had a payment due on {loan.next_due_date} that has not been recorded.',
            dedupe_key=f'loan-overdue:{loan.id}:{loan.next_due_date}',
        )
        flagged += int(created)
    return flagged


@shared_task
def check_budget_alerts(today=None):
    today = today or date.today()
    budgets = Budget.objects.filter(month=today.month, year=today.year)
    sent = 0
    for budget in budgets:
        usage = calculate_budget_usage(budget.amount, get_spent_for_budget(budget), budget.alert_thresholds)
        if not usage['crossed_thresholds']:
            continue

        highest_threshold = max(usage['crossed_thresholds'])
        created = _notify_once(
            budget.user,
            Notification.NotificationType.BUDGET_ALERT,
            title=f'{budget.category} budget at {usage["percentage_used"]}%',
            message=(
                f'Your "{budget.category}" budget for {budget.month}/{budget.year} has reached '
                f'{usage["percentage_used"]}% ({usage["status"]}), crossing the {highest_threshold}% alert threshold.'
            ),
            dedupe_key=f'budget-alert:{budget.id}:{highest_threshold}',
        )
        sent += int(created)
    return sent


@shared_task
def generate_recurring_transactions_for_all_users(today=None):
    User = get_user_model()
    users = User.objects.filter(recurring_transactions__is_active=True).distinct()
    total_generated = 0
    for user in users:
        generated = generate_due_transactions(user, as_of=today)
        total_generated += sum(len(dates) for dates in generated.values())
    return total_generated


@shared_task
def send_monthly_financial_summaries(today=None):
    today = today or date.today()
    User = get_user_model()
    sent = 0
    for user in User.objects.all():
        dedupe_key = f'monthly-summary:{user.id}:{today.year}-{today.month:02d}'
        if Notification.objects.filter(user=user, dedupe_key=dedupe_key).exists():
            continue

        result = get_financial_analytics(user, 'PREVIOUS_MONTH', today=today)
        totals = result['totals']
        if totals['income'] == 0 and totals['expenses'] == 0:
            continue  # nothing to summarize — skip rather than send an empty notification

        message = (
            f"Last month: income {totals['income']}, expenses {totals['expenses']}, "
            f"savings {totals['savings']}, interest paid {totals['interest_paid']}."
        )
        created = _notify_once(
            user, Notification.NotificationType.MONTHLY_SUMMARY,
            title='Your monthly financial summary', message=message, dedupe_key=dedupe_key,
        )
        sent += int(created)
    return sent


def _advance_reminder_date(reminder_date, recurrence):
    return reminder_date + _RECURRENCE_STEP[recurrence]


@shared_task
def process_reminders(today=None):
    today = today or date.today()
    due = Reminder.objects.filter(is_completed=False, reminder_date__lte=today).exclude(snoozed_until__gt=today)
    sent = 0

    for reminder in due:
        if reminder.last_notified_at and reminder.last_notified_at.date() == today:
            continue

        amount_note = f' (₹{reminder.amount})' if reminder.amount else ''
        created = _notify_once(
            reminder.user,
            Notification.NotificationType.CUSTOM_REMINDER,
            title=reminder.description,
            message=f'{reminder.description}{amount_note} was due on {reminder.reminder_date}.',
            dedupe_key=f'reminder:{reminder.id}:{reminder.reminder_date}',
        )
        sent += int(created)

        reminder.last_notified_at = timezone.now()
        if reminder.recurrence == Reminder.Recurrence.NONE:
            reminder.is_completed = True
            reminder.save(update_fields=['is_completed', 'last_notified_at', 'updated_at'])
        else:
            reminder.reminder_date = _advance_reminder_date(reminder.reminder_date, reminder.recurrence)
            reminder.snoozed_until = None
            reminder.save(update_fields=['reminder_date', 'snoozed_until', 'last_notified_at', 'updated_at'])

    return sent
