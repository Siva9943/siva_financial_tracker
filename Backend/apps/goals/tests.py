from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from services.goal_service import GoalContributionError, calculate_goal_progress, record_contribution

from .models import FinancialGoal, GoalContribution

User = get_user_model()

TODAY = date(2026, 1, 1)


class GoalProgressServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def _make_goal(self, **overrides):
        defaults = dict(
            user=self.user, name='Emergency Fund', goal_type=FinancialGoal.GoalType.EMERGENCY_FUND,
            target_amount=Decimal('12000'), current_amount=Decimal('0'),
            target_date=TODAY + relativedelta(months=12), monthly_contribution=Decimal('1000'),
        )
        defaults.update(overrides)
        return FinancialGoal.objects.create(**defaults)

    def test_on_track_goal(self):
        goal = self._make_goal()
        progress = calculate_goal_progress(goal, today=TODAY)
        self.assertEqual(progress['remaining_amount'], Decimal('12000.00'))
        self.assertEqual(progress['required_monthly_contribution'], Decimal('1000.00'))
        self.assertEqual(progress['estimated_completion_date'], TODAY + relativedelta(months=12))
        self.assertTrue(progress['is_on_track'])

    def test_off_track_goal_when_contribution_too_small(self):
        goal = self._make_goal(monthly_contribution=Decimal('500'))
        progress = calculate_goal_progress(goal, today=TODAY)
        self.assertEqual(progress['estimated_completion_date'], TODAY + relativedelta(months=24))
        self.assertFalse(progress['is_on_track'])

    def test_percentage_complete(self):
        goal = self._make_goal(current_amount=Decimal('3000'))
        progress = calculate_goal_progress(goal, today=TODAY)
        self.assertEqual(progress['percentage_complete'], 25.0)
        self.assertEqual(progress['remaining_amount'], Decimal('9000.00'))

    def test_already_funded_goal(self):
        goal = self._make_goal(current_amount=Decimal('12000'))
        progress = calculate_goal_progress(goal, today=TODAY)
        self.assertEqual(progress['remaining_amount'], Decimal('0.00'))
        self.assertEqual(progress['required_monthly_contribution'], Decimal('0.00'))
        self.assertEqual(progress['estimated_completion_date'], TODAY)

    def test_zero_monthly_contribution_has_no_projection(self):
        goal = self._make_goal(monthly_contribution=Decimal('0'))
        progress = calculate_goal_progress(goal, today=TODAY)
        self.assertIsNone(progress['estimated_completion_date'])
        self.assertFalse(progress['is_on_track'])


class GoalContributionServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.goal = FinancialGoal.objects.create(
            user=self.user, name='Vacation', goal_type=FinancialGoal.GoalType.VACATION,
            target_amount=Decimal('1000'), current_amount=Decimal('0'),
            target_date=TODAY + relativedelta(months=6), monthly_contribution=Decimal('200'),
        )

    def test_contribution_increases_current_amount(self):
        record_contribution(self.goal, amount=Decimal('300'), contribution_date=TODAY)
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.current_amount, Decimal('300.00'))
        self.assertEqual(GoalContribution.objects.count(), 1)

    def test_goal_auto_completes_when_target_reached(self):
        record_contribution(self.goal, amount=Decimal('1000'), contribution_date=TODAY)
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, FinancialGoal.Status.COMPLETED)

    def test_overshooting_contribution_still_completes(self):
        record_contribution(self.goal, amount=Decimal('1500'), contribution_date=TODAY)
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, FinancialGoal.Status.COMPLETED)
        self.assertEqual(self.goal.current_amount, Decimal('1500.00'))

    def test_zero_amount_rejected(self):
        with self.assertRaises(GoalContributionError):
            record_contribution(self.goal, amount=Decimal('0'), contribution_date=TODAY)

    def test_cannot_contribute_to_completed_goal(self):
        self.goal.status = FinancialGoal.Status.COMPLETED
        self.goal.save(update_fields=['status'])
        with self.assertRaises(GoalContributionError):
            record_contribution(self.goal, amount=Decimal('100'), contribution_date=TODAY)

    def test_cannot_contribute_to_abandoned_goal(self):
        self.goal.status = FinancialGoal.Status.ABANDONED
        self.goal.save(update_fields=['status'])
        with self.assertRaises(GoalContributionError):
            record_contribution(self.goal, amount=Decimal('100'), contribution_date=TODAY)


class FinancialGoalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.list_url = reverse('goal-list')

    def _payload(self, **overrides):
        payload = {
            'name': 'Emergency Fund', 'goal_type': 'EMERGENCY_FUND', 'target_amount': '12000',
            'target_date': '2027-01-01', 'monthly_contribution': '1000',
        }
        payload.update(overrides)
        return payload

    def test_create_goal_defaults_status_in_progress(self):
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['status'], 'IN_PROGRESS')
        self.assertIn('remaining_amount', response.data)
        self.assertIn('estimated_completion_date', response.data)

    def test_target_amount_must_be_positive(self):
        response = self.client.post(self.list_url, self._payload(target_amount='0'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_monthly_contribution_rejected(self):
        response = self.client.post(self.list_url, self._payload(monthly_contribution='-100'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_returns_own_goals(self):
        self.client.post(self.list_url, self._payload())
        FinancialGoal.objects.create(
            user=self.other_user, name='House', goal_type='HOUSE', target_amount=Decimal('500000'),
            target_date=date(2030, 1, 1),
        )
        response = self.client.get(self.list_url)
        names = [g['name'] for g in response.data['results']]
        self.assertNotIn('House', names)

    def test_cannot_access_other_users_goal(self):
        other_goal = FinancialGoal.objects.create(
            user=self.other_user, name='House', goal_type='HOUSE', target_amount=Decimal('500000'),
            target_date=date(2030, 1, 1),
        )
        response = self.client.get(reverse('goal-detail', args=[other_goal.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_record_contribution_via_api(self):
        create_response = self.client.post(self.list_url, self._payload())
        goal_id = create_response.data['id']

        response = self.client.post(
            reverse('goal-contributions', args=[goal_id]), {'amount': '500', 'contribution_date': '2026-02-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['goal']['current_amount'], '500.00')

    def test_list_contributions_via_api(self):
        create_response = self.client.post(self.list_url, self._payload())
        goal_id = create_response.data['id']
        self.client.post(reverse('goal-contributions', args=[goal_id]), {'amount': '500', 'contribution_date': '2026-02-01'})

        response = self.client.get(reverse('goal-contributions', args=[goal_id]))
        self.assertEqual(len(response.data['results']), 1)

    def test_contribution_to_completed_goal_returns_400(self):
        create_response = self.client.post(self.list_url, self._payload(target_amount='100'))
        goal_id = create_response.data['id']
        self.client.post(reverse('goal-contributions', args=[goal_id]), {'amount': '100', 'contribution_date': '2026-02-01'})

        response = self.client.post(reverse('goal-contributions', args=[goal_id]), {'amount': '50', 'contribution_date': '2026-03-01'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_contribute_to_other_users_goal(self):
        other_goal = FinancialGoal.objects.create(
            user=self.other_user, name='House', goal_type='HOUSE', target_amount=Decimal('500000'),
            target_date=date(2030, 1, 1),
        )
        response = self.client.post(
            reverse('goal-contributions', args=[other_goal.id]), {'amount': '100', 'contribution_date': '2026-02-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
