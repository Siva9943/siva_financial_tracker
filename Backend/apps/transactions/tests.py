from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from services.transaction_service import generate_due_transactions

from .aggregations import category_breakdown, monthly_trend, monthly_trend_by_type, period_totals
from .models import RecurringTransaction, Transaction

User = get_user_model()


class TransactionCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.list_url = reverse('transaction-list')

    def _create(self, **overrides):
        payload = {
            'transaction_type': Transaction.TransactionType.EXPENSE,
            'amount': '100.50',
            'category': 'Food',
            'description': 'Lunch',
            'transaction_date': '2026-01-15',
            'payment_method': Transaction.PaymentMethod.CASH,
        }
        payload.update(overrides)
        return self.client.post(self.list_url, payload)

    def test_create_transaction(self):
        response = self._create()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.first().user, self.user)

    def test_amount_must_be_positive(self):
        response = self._create(amount='0')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self._create(amount='-5')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_category_required(self):
        response = self._create(category='  ')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_returns_own_transactions(self):
        self._create()
        other_txn = Transaction.objects.create(
            user=self.other_user,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=500,
            category='Salary',
            transaction_date=date(2026, 1, 1),
        )

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item['id'] for item in response.data['results']]
        self.assertNotIn(other_txn.id, returned_ids)

    def test_cannot_retrieve_or_modify_other_users_transaction(self):
        other_txn = Transaction.objects.create(
            user=self.other_user,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=500,
            category='Salary',
            transaction_date=date(2026, 1, 1),
        )
        detail_url = reverse('transaction-detail', args=[other_txn.id])

        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_update_and_delete_own_transaction(self):
        create_response = self._create()
        txn_id = create_response.data['id']
        detail_url = reverse('transaction-detail', args=[txn_id])

        update_response = self.client.patch(detail_url, {'amount': '200.00'})
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['amount'], '200.00')

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_filter_by_type_and_date_range(self):
        self._create(transaction_type=Transaction.TransactionType.EXPENSE, transaction_date='2026-01-05')
        self._create(transaction_type=Transaction.TransactionType.INCOME, category='Salary', transaction_date='2026-02-10')

        response = self.client.get(self.list_url, {'transaction_type': 'INCOME'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['transaction_type'], 'INCOME')

        response = self.client.get(self.list_url, {'date_from': '2026-02-01', 'date_to': '2026-02-28'})
        self.assertEqual(len(response.data['results']), 1)

    def test_search_by_description(self):
        self._create(description='Grocery run')
        self._create(description='Movie night', category='Entertainment')

        response = self.client.get(self.list_url, {'search': 'Movie'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['description'], 'Movie night')

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class IncomeExpenseEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.client.force_authenticate(self.user)
        self.income_url = reverse('income-list')
        self.expense_url = reverse('expense-list')

    def test_income_endpoint_locks_transaction_type(self):
        response = self.client.post(
            self.income_url,
            {
                'transaction_type': 'EXPENSE',  # should be ignored — endpoint forces INCOME
                'amount': '5000.00',
                'category': 'Salary',
                'transaction_date': '2026-03-01',
                'payment_method': 'BANK_TRANSFER',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Transaction.objects.get().transaction_type, Transaction.TransactionType.INCOME)

    def test_expense_list_excludes_income(self):
        self.client.post(
            self.income_url,
            {'amount': '5000', 'category': 'Salary', 'transaction_date': '2026-03-01'},
        )
        self.client.post(
            self.expense_url,
            {'amount': '200', 'category': 'Food', 'transaction_date': '2026-03-02'},
        )

        response = self.client.get(self.expense_url)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['category'], 'Food')

    def test_summary_action_reflects_todays_transaction(self):
        today = date.today().isoformat()
        self.client.post(self.expense_url, {'amount': '75', 'category': 'Food', 'transaction_date': today})

        response = self.client.get(reverse('expense-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data['totals']['today'])), Decimal('75'))
        self.assertIn('monthly_trend', response.data)
        self.assertEqual(len(response.data['monthly_trend']), 6)

    def test_transaction_summary_action_returns_monthly_trend_by_type(self):
        today = date.today().isoformat()
        self.client.post(self.income_url, {'amount': '5000', 'category': 'Salary', 'transaction_date': today})
        self.client.post(self.expense_url, {'amount': '75', 'category': 'Food', 'transaction_date': today})

        response = self.client.get(reverse('transaction-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['monthly_trend']), 6)
        current_month = response.data['monthly_trend'][-1]
        self.assertEqual(Decimal(str(current_month['income'])), Decimal('5000'))
        self.assertEqual(Decimal(str(current_month['expense'])), Decimal('75'))


class AggregationHelperTests(TestCase):
    """Pure unit tests against a fixed reference date to avoid flakiness."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.today = date(2026, 3, 18)  # Wednesday
        self.start_of_week = date(2026, 3, 16)  # Monday of that week

        self.amounts = {
            self.today: Decimal('100'),
            self.start_of_week: Decimal('50'),
            date(2026, 3, 1): Decimal('25'),
            date(2026, 1, 10): Decimal('10'),
            date(2025, 6, 15): Decimal('5'),
        }
        for txn_date, amount in self.amounts.items():
            Transaction.objects.create(
                user=self.user,
                transaction_type=Transaction.TransactionType.EXPENSE,
                amount=amount,
                category='Food',
                transaction_date=txn_date,
            )

    def test_period_totals_boundaries(self):
        totals = period_totals(Transaction.objects.filter(user=self.user), today=self.today)
        self.assertEqual(totals['today'], Decimal('100'))
        self.assertEqual(totals['this_week'], Decimal('150'))
        self.assertEqual(totals['this_month'], Decimal('175'))
        self.assertEqual(totals['this_year'], Decimal('185'))

    def test_category_breakdown_percentages(self):
        Transaction.objects.create(
            user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal('50'),
            category='Travel',
            transaction_date=self.today,
        )
        breakdown = category_breakdown(Transaction.objects.filter(user=self.user))
        by_category = {row['category']: row for row in breakdown}
        self.assertEqual(by_category['Food']['total'], Decimal('190'))
        self.assertEqual(by_category['Travel']['total'], Decimal('50'))
        self.assertAlmostEqual(sum(row['percentage'] for row in breakdown), 100, delta=0.1)

    def test_monthly_trend_is_zero_filled_and_ordered(self):
        trend = monthly_trend(Transaction.objects.filter(user=self.user), months=6, today=self.today)
        self.assertEqual(len(trend), 6)
        self.assertEqual([row['month'] for row in trend], ['2025-10', '2025-11', '2025-12', '2026-01', '2026-02', '2026-03'])
        by_month = {row['month']: row['total'] for row in trend}
        self.assertEqual(by_month['2026-03'], Decimal('175'))
        self.assertEqual(by_month['2026-01'], Decimal('10'))
        self.assertEqual(by_month['2025-11'], 0)

    def test_monthly_trend_by_type_splits_income_and_expense(self):
        Transaction.objects.create(
            user=self.user,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('300'),
            category='Salary',
            transaction_date=self.today,
        )
        trend = monthly_trend_by_type(Transaction.objects.filter(user=self.user), months=6, today=self.today)
        current_month = trend[-1]
        self.assertEqual(current_month['month'], '2026-03')
        self.assertEqual(current_month['income'], Decimal('300'))
        self.assertEqual(current_month['expense'], Decimal('175'))


class RecurringTransactionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.client.force_authenticate(self.user)

    def _make_rule(self, **overrides):
        defaults = dict(
            user=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal('1000'),
            category='Rent',
            frequency=RecurringTransaction.Frequency.MONTHLY,
            start_date=date(2026, 1, 31),
            next_run_date=date(2026, 1, 31),
        )
        defaults.update(overrides)
        return RecurringTransaction.objects.create(**defaults)

    def test_generate_due_handles_month_end_and_catches_up(self):
        rule = self._make_rule()

        generated = generate_due_transactions(self.user, as_of=date(2026, 3, 15))

        self.assertEqual(generated[rule.id], [date(2026, 1, 31), date(2026, 2, 28)])
        rule.refresh_from_db()
        self.assertEqual(rule.next_run_date, date(2026, 3, 28))
        self.assertEqual(Transaction.objects.filter(recurring_transaction=rule).count(), 2)

    def test_generate_due_is_idempotent_for_same_date(self):
        rule = self._make_rule()
        generate_due_transactions(self.user, as_of=date(2026, 1, 31))

        rule.refresh_from_db()
        rule.next_run_date = date(2026, 1, 31)  # simulate a retry/duplicate trigger
        rule.save(update_fields=['next_run_date'])
        generate_due_transactions(self.user, as_of=date(2026, 1, 31))

        self.assertEqual(
            Transaction.objects.filter(recurring_transaction=rule, transaction_date=date(2026, 1, 31)).count(), 1
        )

    def test_generate_due_deactivates_after_end_date(self):
        rule = self._make_rule(
            frequency=RecurringTransaction.Frequency.DAILY,
            start_date=date(2026, 1, 1),
            next_run_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )

        generate_due_transactions(self.user, as_of=date(2026, 1, 10))

        rule.refresh_from_db()
        self.assertFalse(rule.is_active)
        self.assertEqual(Transaction.objects.filter(recurring_transaction=rule).count(), 3)

    def test_generate_due_endpoint(self):
        self._make_rule(next_run_date=date.today())

        response = self.client.post(reverse('recurring-transaction-generate-due'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)

    def test_create_recurring_rule_via_api_defaults_next_run_date(self):
        url = reverse('recurring-transaction-list')
        response = self.client.post(
            url,
            {
                'transaction_type': 'EXPENSE',
                'amount': '1200',
                'category': 'Rent',
                'frequency': 'MONTHLY',
                'start_date': '2026-09-01',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['next_run_date'], '2026-09-01')

    def test_end_date_must_be_after_start_date(self):
        url = reverse('recurring-transaction-list')
        response = self.client.post(
            url,
            {
                'transaction_type': 'EXPENSE',
                'amount': '100',
                'category': 'Rent',
                'frequency': 'MONTHLY',
                'start_date': '2026-01-31',
                'end_date': '2026-01-01',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
