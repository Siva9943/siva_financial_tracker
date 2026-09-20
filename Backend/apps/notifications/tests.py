from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.budgets.models import Budget
from apps.loans.models import Loan
from apps.transactions.models import Transaction

from . import tasks
from .models import Notification, Reminder

User = get_user_model()


class EmiReminderTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def _make_loan(self, next_due_date, **overrides):
        defaults = dict(
            user=self.user, loan_name='Home Loan', loan_type=Loan.LoanType.HOME,
            original_principal=Decimal('100000'), outstanding_principal=Decimal('100000'),
            annual_interest_rate=Decimal('10'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            emi_amount=Decimal('5000'), start_date=date(2026, 1, 1), maturity_date=date(2030, 1, 1),
            next_due_date=next_due_date,
        )
        defaults.update(overrides)
        return Loan.objects.create(**defaults)

    def test_sends_reminder_for_loan_due_within_lead_time(self):
        loan = self._make_loan(next_due_date=date(2026, 3, 12))
        sent = tasks.send_emi_reminders(today=date(2026, 3, 10))
        self.assertEqual(sent, 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, Notification.NotificationType.EMI_REMINDER)
        self.assertIn(loan.loan_name, notification.title)

    def test_no_reminder_for_loan_due_far_in_future(self):
        self._make_loan(next_due_date=date(2026, 4, 30))
        sent = tasks.send_emi_reminders(today=date(2026, 3, 10))
        self.assertEqual(sent, 0)

    def test_running_twice_does_not_duplicate(self):
        self._make_loan(next_due_date=date(2026, 3, 12))
        tasks.send_emi_reminders(today=date(2026, 3, 10))
        second_run_sent = tasks.send_emi_reminders(today=date(2026, 3, 10))
        self.assertEqual(second_run_sent, 0)
        self.assertEqual(Notification.objects.count(), 1)


class OverdueDetectionTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.loan = Loan.objects.create(
            user=self.user, loan_name='Car Loan', loan_type=Loan.LoanType.VEHICLE,
            original_principal=Decimal('50000'), outstanding_principal=Decimal('50000'),
            annual_interest_rate=Decimal('9'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2029, 1, 1), next_due_date=date(2026, 3, 1),
        )

    def test_flags_overdue_loan_and_notifies(self):
        flagged = tasks.detect_overdue_loans(today=date(2026, 3, 15))
        self.assertEqual(flagged, 1)
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.status, Loan.Status.OVERDUE)
        self.assertEqual(Notification.objects.count(), 1)

    def test_does_not_flag_loan_not_yet_due(self):
        flagged = tasks.detect_overdue_loans(today=date(2026, 2, 15))
        self.assertEqual(flagged, 0)
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.status, Loan.Status.ACTIVE)

    def test_running_twice_does_not_duplicate_notification(self):
        tasks.detect_overdue_loans(today=date(2026, 3, 15))
        # Loan is now OVERDUE, so a second run shouldn't even re-match the ACTIVE filter — but
        # simulate a re-run against the same due date directly to prove the dedupe key holds.
        self.loan.status = Loan.Status.ACTIVE
        self.loan.save(update_fields=['status'])
        second_flagged = tasks.detect_overdue_loans(today=date(2026, 3, 15))
        self.assertEqual(second_flagged, 0)
        self.assertEqual(Notification.objects.count(), 1)


class BudgetAlertTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.budget = Budget.objects.create(user=self.user, category='Food', amount=Decimal('1000'), month=3, year=2026)

    def _spend(self, amount, txn_date=date(2026, 3, 10)):
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal(amount), category='Food', transaction_date=txn_date,
        )

    def test_no_alert_when_under_lowest_threshold(self):
        self._spend('200')
        sent = tasks.check_budget_alerts(today=date(2026, 3, 15))
        self.assertEqual(sent, 0)

    def test_alert_when_threshold_crossed(self):
        self._spend('600')
        sent = tasks.check_budget_alerts(today=date(2026, 3, 15))
        self.assertEqual(sent, 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, Notification.NotificationType.BUDGET_ALERT)
        self.assertIn('50%', notification.message)

    def test_running_twice_does_not_duplicate(self):
        self._spend('600')
        tasks.check_budget_alerts(today=date(2026, 3, 15))
        second_sent = tasks.check_budget_alerts(today=date(2026, 3, 15))
        self.assertEqual(second_sent, 0)
        self.assertEqual(Notification.objects.count(), 1)

    def test_new_alert_when_higher_threshold_crossed_later(self):
        self._spend('600')  # crosses 50%
        tasks.check_budget_alerts(today=date(2026, 3, 15))
        self._spend('300')  # now at 90%, crosses 75% and 90%
        tasks.check_budget_alerts(today=date(2026, 3, 20))
        self.assertEqual(Notification.objects.count(), 2)


class MonthlySummaryTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def test_no_summary_when_no_activity(self):
        sent = tasks.send_monthly_financial_summaries(today=date(2026, 4, 1))
        self.assertEqual(sent, 0)

    def test_summary_sent_when_activity_exists(self):
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('5000'), category='Salary', transaction_date=date(2026, 3, 10),
        )
        sent = tasks.send_monthly_financial_summaries(today=date(2026, 4, 1))
        self.assertEqual(sent, 1)
        self.assertEqual(Notification.objects.get().notification_type, Notification.NotificationType.MONTHLY_SUMMARY)

    def test_running_twice_same_month_does_not_duplicate(self):
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('5000'), category='Salary', transaction_date=date(2026, 3, 10),
        )
        tasks.send_monthly_financial_summaries(today=date(2026, 4, 1))
        second_sent = tasks.send_monthly_financial_summaries(today=date(2026, 4, 1))
        self.assertEqual(second_sent, 0)
        self.assertEqual(Notification.objects.count(), 1)


class ReminderTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def test_one_time_reminder_notifies_and_completes(self):
        reminder = Reminder.objects.create(
            user=self.user, reminder_type=Reminder.ReminderType.RENT, description='Pay rent',
            amount=Decimal('15000'), reminder_date=date(2026, 3, 1),
        )
        sent = tasks.process_reminders(today=date(2026, 3, 1))
        self.assertEqual(sent, 1)
        reminder.refresh_from_db()
        self.assertTrue(reminder.is_completed)
        self.assertIsNotNone(reminder.last_notified_at)

    def test_recurring_reminder_advances_date_and_stays_incomplete(self):
        reminder = Reminder.objects.create(
            user=self.user, reminder_type=Reminder.ReminderType.RENT, description='Pay rent',
            reminder_date=date(2026, 3, 1), recurrence=Reminder.Recurrence.MONTHLY,
        )
        tasks.process_reminders(today=date(2026, 3, 1))
        reminder.refresh_from_db()
        self.assertFalse(reminder.is_completed)
        self.assertEqual(reminder.reminder_date, date(2026, 4, 1))

    def test_snoozed_reminder_is_skipped(self):
        Reminder.objects.create(
            user=self.user, reminder_type=Reminder.ReminderType.CUSTOM, description='Renew subscription',
            reminder_date=date(2026, 3, 1), snoozed_until=date(2026, 3, 10),
        )
        sent = tasks.process_reminders(today=date(2026, 3, 5))
        self.assertEqual(sent, 0)

    def test_snoozed_reminder_fires_once_snooze_expires(self):
        Reminder.objects.create(
            user=self.user, reminder_type=Reminder.ReminderType.CUSTOM, description='Renew subscription',
            reminder_date=date(2026, 3, 1), snoozed_until=date(2026, 3, 10),
        )
        sent = tasks.process_reminders(today=date(2026, 3, 11))
        self.assertEqual(sent, 1)

    def test_running_twice_same_day_does_not_duplicate(self):
        Reminder.objects.create(
            user=self.user, reminder_type=Reminder.ReminderType.RENT, description='Pay rent',
            reminder_date=date(2026, 3, 1), recurrence=Reminder.Recurrence.MONTHLY,
        )
        tasks.process_reminders(today=date(2026, 3, 1))
        second_sent = tasks.process_reminders(today=date(2026, 3, 1))
        self.assertEqual(second_sent, 0)
        self.assertEqual(Notification.objects.count(), 1)

    def test_completed_reminder_is_never_processed(self):
        Reminder.objects.create(
            user=self.user, reminder_type=Reminder.ReminderType.RENT, description='Pay rent',
            reminder_date=date(2026, 3, 1), is_completed=True,
        )
        sent = tasks.process_reminders(today=date(2026, 3, 5))
        self.assertEqual(sent, 0)


class RecurringTransactionsTaskTests(TestCase):
    def test_generates_via_existing_service_and_counts_results(self):
        from apps.transactions.models import RecurringTransaction

        user = User.objects.create_user(username='alice', password='pass12345')
        RecurringTransaction.objects.create(
            user=user, transaction_type=Transaction.TransactionType.EXPENSE, amount=Decimal('1200'),
            category='Rent', frequency=RecurringTransaction.Frequency.MONTHLY,
            start_date=date(2026, 1, 1), next_run_date=date(2026, 1, 1),
        )
        total = tasks.generate_recurring_transactions_for_all_users(today=date(2026, 3, 15))
        self.assertEqual(total, 3)  # Jan, Feb, Mar


class ReminderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.list_url = reverse('reminder-list')

    def test_create_reminder(self):
        response = self.client.post(self.list_url, {
            'reminder_type': 'RENT', 'description': 'Pay rent', 'amount': '15000', 'reminder_date': '2026-04-01',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_description_required(self):
        response = self.client.post(self.list_url, {'reminder_type': 'RENT', 'description': '  ', 'reminder_date': '2026-04-01'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_snooze_action(self):
        create_response = self.client.post(self.list_url, {'reminder_type': 'RENT', 'description': 'Pay rent', 'reminder_date': '2026-04-01'})
        reminder_id = create_response.data['id']

        response = self.client.post(reverse('reminder-snooze', args=[reminder_id]), {'snoozed_until': '2099-01-01'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['snoozed_until'], '2099-01-01')

    def test_snooze_rejects_past_date(self):
        create_response = self.client.post(self.list_url, {'reminder_type': 'RENT', 'description': 'Pay rent', 'reminder_date': '2026-04-01'})
        reminder_id = create_response.data['id']

        response = self.client.post(reverse('reminder-snooze', args=[reminder_id]), {'snoozed_until': '2000-01-01'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_action(self):
        create_response = self.client.post(self.list_url, {'reminder_type': 'RENT', 'description': 'Pay rent', 'reminder_date': '2026-04-01'})
        reminder_id = create_response.data['id']

        response = self.client.post(reverse('reminder-complete', args=[reminder_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_completed'])

    def test_cannot_access_other_users_reminder(self):
        other_reminder = Reminder.objects.create(
            user=self.other_user, reminder_type=Reminder.ReminderType.RENT, description='Pay rent', reminder_date=date(2026, 4, 1),
        )
        response = self.client.get(reverse('reminder-detail', args=[other_reminder.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)

        Notification.objects.create(user=self.user, notification_type='CUSTOM_REMINDER', title='A', message='a', dedupe_key='a')
        Notification.objects.create(user=self.user, notification_type='CUSTOM_REMINDER', title='B', message='b', dedupe_key='b')
        Notification.objects.create(user=self.other_user, notification_type='CUSTOM_REMINDER', title='C', message='c', dedupe_key='c')

    def test_list_only_returns_own_notifications(self):
        response = self.client.get(reverse('notification-list'))
        self.assertEqual(response.data['count'], 2)

    def test_unread_count(self):
        response = self.client.get(reverse('notification-unread-count'))
        self.assertEqual(response.data['count'], 2)

    def test_mark_read(self):
        notification = Notification.objects.filter(user=self.user).first()
        response = self.client.post(reverse('notification-mark-read', args=[notification.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])

    def test_mark_all_read(self):
        response = self.client.post(reverse('notification-mark-all-read'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_cannot_mark_other_users_notification_read(self):
        other_notification = Notification.objects.get(user=self.other_user)
        response = self.client.post(reverse('notification-mark-read', args=[other_notification.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse('notification-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
