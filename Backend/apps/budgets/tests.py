from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.transactions.models import Transaction
from services.budget_service import build_spent_lookup, calculate_budget_usage, get_spent_for_budget

from .models import Budget

User = get_user_model()


class BudgetUsageServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def _spend(self, category, amount, txn_date):
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal(amount), category=category, transaction_date=txn_date,
        )

    def test_get_spent_for_budget_sums_matching_expenses_only(self):
        budget = Budget.objects.create(user=self.user, category='Food', amount=Decimal('1000'), month=3, year=2026)
        self._spend('Food', '200', date(2026, 3, 5))
        self._spend('Food', '150', date(2026, 3, 20))
        self._spend('Food', '999', date(2026, 4, 1))  # different month — excluded
        self._spend('Travel', '500', date(2026, 3, 10))  # different category — excluded
        self._spend('Food', '999', date(2025, 3, 10))  # different year — excluded

        self.assertEqual(get_spent_for_budget(budget), Decimal('350.00'))

    def test_build_spent_lookup_groups_by_category_month_year(self):
        self._spend('Food', '200', date(2026, 3, 5))
        self._spend('Travel', '100', date(2026, 3, 5))
        self._spend('Food', '50', date(2026, 4, 5))

        march_budget = Budget(user=self.user, category='Food', month=3, year=2026)
        april_budget = Budget(user=self.user, category='Food', month=4, year=2026)
        lookup = build_spent_lookup(self.user, [march_budget, april_budget])

        self.assertEqual(lookup[('Food', 3, 2026)], Decimal('200.00'))
        self.assertEqual(lookup[('Travel', 3, 2026)], Decimal('100.00'))
        self.assertEqual(lookup[('Food', 4, 2026)], Decimal('50.00'))

    def test_calculate_budget_usage_ok(self):
        result = calculate_budget_usage(Decimal('1000'), Decimal('200'), [50, 75, 90, 100])
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['percentage_used'], 20.0)
        self.assertEqual(result['remaining'], Decimal('800.00'))
        self.assertEqual(result['crossed_thresholds'], [])

    def test_calculate_budget_usage_approaching(self):
        result = calculate_budget_usage(Decimal('1000'), Decimal('600'), [50, 75, 90, 100])
        self.assertEqual(result['status'], 'APPROACHING')
        self.assertEqual(result['crossed_thresholds'], [50])

    def test_calculate_budget_usage_exceeded(self):
        result = calculate_budget_usage(Decimal('1000'), Decimal('1200'), [50, 75, 90, 100])
        self.assertEqual(result['status'], 'EXCEEDED')
        self.assertEqual(result['remaining'], Decimal('-200.00'))
        self.assertEqual(result['crossed_thresholds'], [50, 75, 90, 100])

    def test_calculate_budget_usage_no_spending(self):
        result = calculate_budget_usage(Decimal('1000'), None, [50, 75, 90, 100])
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['spent'], Decimal('0.00'))


class BudgetAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.list_url = reverse('budget-list')

    def _payload(self, **overrides):
        payload = {'category': 'Food', 'amount': '1000', 'month': 3, 'year': 2026}
        payload.update(overrides)
        return payload

    def test_create_budget_defaults_thresholds(self):
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['alert_thresholds'], [50, 75, 90, 100])
        self.assertEqual(response.data['spent'], Decimal('0.00'))
        self.assertEqual(response.data['status'], 'OK')

    def test_amount_must_be_positive(self):
        response = self.client.post(self.list_url, self._payload(amount='0'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_month_must_be_in_range(self):
        response = self.client.post(self.list_url, self._payload(month=13))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_category_month_year_rejected(self):
        self.client.post(self.list_url, self._payload())
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_category_different_month_allowed(self):
        self.client.post(self.list_url, self._payload(month=3))
        response = self.client.post(self.list_url, self._payload(month=4))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_threshold_rejected(self):
        response = self.client.post(self.list_url, self._payload(alert_thresholds=[0, 150]), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_includes_usage_reflecting_actual_spending(self):
        self.client.post(self.list_url, self._payload())
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal('600'), category='Food', transaction_date=date(2026, 3, 10),
        )

        response = self.client.get(self.list_url, {'month': 3, 'year': 2026})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        budget_data = response.data['results'][0]
        self.assertEqual(budget_data['spent'], Decimal('600.00'))
        self.assertEqual(budget_data['remaining'], Decimal('400.00'))
        self.assertEqual(budget_data['percentage_used'], 60.0)
        self.assertEqual(budget_data['status'], 'APPROACHING')

    def test_list_only_returns_own_budgets(self):
        self.client.post(self.list_url, self._payload())
        Budget.objects.create(user=self.other_user, category='Travel', amount=Decimal('500'), month=3, year=2026)

        response = self.client.get(self.list_url)
        categories = [b['category'] for b in response.data['results']]
        self.assertNotIn('Travel', categories)

    def test_cannot_access_other_users_budget(self):
        other_budget = Budget.objects.create(user=self.other_user, category='Travel', amount=Decimal('500'), month=3, year=2026)
        detail_url = reverse('budget-detail', args=[other_budget.id])
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_category_and_year(self):
        self.client.post(self.list_url, self._payload(category='Food', month=3, year=2026))
        self.client.post(self.list_url, self._payload(category='Travel', month=3, year=2026))

        response = self.client.get(self.list_url, {'category': 'Travel'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['category'], 'Travel')

    def test_update_budget(self):
        create_response = self.client.post(self.list_url, self._payload())
        budget_id = create_response.data['id']
        detail_url = reverse('budget-detail', args=[budget_id])

        response = self.client.patch(detail_url, {'amount': '2000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '2000.00')

    def test_delete_budget(self):
        create_response = self.client.post(self.list_url, self._payload())
        budget_id = create_response.data['id']
        detail_url = reverse('budget-detail', args=[budget_id])

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Budget.objects.count(), 0)

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
