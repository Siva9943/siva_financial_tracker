from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.loans.models import Loan
from services.repayment_service import RepaymentPlanError, generate_repayment_plan

from .models import RepaymentPlan

User = get_user_model()


class RepaymentServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.loan_a = self._make_loan('A', rate='12', outstanding='1200', emi='200')
        self.loan_b = self._make_loan('B', rate='6', outstanding='2000', emi='200')

    def _make_loan(self, name, *, rate, outstanding, emi, **overrides):
        defaults = dict(
            user=self.user,
            loan_name=name,
            loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal(outstanding),
            outstanding_principal=Decimal(outstanding),
            annual_interest_rate=Decimal(rate),
            interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            payment_frequency=Loan.PaymentFrequency.MONTHLY,
            emi_amount=Decimal(emi),
            start_date=date(2026, 1, 1),
            maturity_date=date(2030, 1, 1),
        )
        defaults.update(overrides)
        return Loan.objects.create(**defaults)

    def _generate(self, **overrides):
        params = dict(
            strategy='AVALANCHE',
            monthly_income=Decimal('1000'),
            essential_expenses=Decimal('400'),
            emergency_savings_allocation=Decimal('0'),
            extra_payment=Decimal('100'),
            as_of=date(2026, 1, 1),
        )
        params.update(overrides)
        return generate_repayment_plan(Loan.objects.filter(user=self.user), **params)

    def test_first_month_avalanche_sends_extra_to_higher_rate_loan(self):
        result = self._generate()
        month1 = [item for item in result['items'] if item['month_number'] == 1]
        by_loan = {item['loan_name']: item for item in month1}

        self.assertEqual(by_loan['A']['interest_paid'], Decimal('12.00'))
        self.assertEqual(by_loan['A']['extra_payment'], Decimal('100.00'))
        self.assertEqual(by_loan['A']['principal_paid'], Decimal('288.00'))
        self.assertEqual(by_loan['A']['closing_balance'], Decimal('912.00'))

        self.assertEqual(by_loan['B']['interest_paid'], Decimal('10.00'))
        self.assertEqual(by_loan['B']['extra_payment'], Decimal('0.00'))
        self.assertEqual(by_loan['B']['principal_paid'], Decimal('190.00'))
        self.assertEqual(by_loan['B']['closing_balance'], Decimal('1810.00'))

    def test_principal_paid_across_all_months_equals_original_balance(self):
        result = self._generate()
        for loan_name, original in (('A', Decimal('1200')), ('B', Decimal('2000'))):
            total_principal = sum(
                (item['principal_paid'] for item in result['items'] if item['loan_name'] == loan_name), Decimal('0.00')
            )
            self.assertEqual(total_principal, original)

    def test_last_item_per_loan_has_zero_closing_balance(self):
        result = self._generate()
        for loan_name in ('A', 'B'):
            loan_items = [item for item in result['items'] if item['loan_name'] == loan_name]
            self.assertEqual(loan_items[-1]['closing_balance'], Decimal('0.00'))

    def test_capacity_redirects_to_next_loan_after_payoff(self):
        result = self._generate()
        a_items = [item for item in result['items'] if item['loan_name'] == 'A']
        a_final_month = a_items[-1]['month_number']

        b_items_by_month = {item['month_number']: item for item in result['items'] if item['loan_name'] == 'B'}
        # The month after A closes, B should start receiving the redirected extra payment capacity.
        self.assertGreater(b_items_by_month[a_final_month + 1]['extra_payment'], Decimal('0.00'))

    def test_months_remaining_matches_last_month_number(self):
        result = self._generate()
        self.assertEqual(result['months_remaining'], max(item['month_number'] for item in result['items']))

    def test_total_interest_and_payment_are_consistent(self):
        result = self._generate()
        expected_interest = sum((item['interest_paid'] for item in result['items']), Decimal('0.00'))
        expected_payment = sum(
            (item['principal_paid'] + item['interest_paid'] for item in result['items']), Decimal('0.00')
        )
        self.assertEqual(result['total_interest'], expected_interest)
        self.assertEqual(result['total_payment'], expected_payment)

    def test_snowball_sends_extra_to_smaller_balance(self):
        result = self._generate(strategy='SNOWBALL')
        month1 = {item['loan_name']: item for item in result['items'] if item['month_number'] == 1}
        self.assertGreater(month1['A']['extra_payment'], Decimal('0.00'))  # A has the smaller balance (1200 < 2000)
        self.assertEqual(month1['B']['extra_payment'], Decimal('0.00'))

    def test_custom_strategy_respects_priority_order(self):
        self.loan_b.priority_order = 1
        self.loan_b.save(update_fields=['priority_order'])
        self.loan_a.priority_order = 2
        self.loan_a.save(update_fields=['priority_order'])

        result = self._generate(strategy='CUSTOM')
        month1 = {item['loan_name']: item for item in result['items'] if item['month_number'] == 1}
        self.assertGreater(month1['B']['extra_payment'], Decimal('0.00'))
        self.assertEqual(month1['A']['extra_payment'], Decimal('0.00'))

    def test_zero_extra_payment_still_completes(self):
        result = self._generate(extra_payment=Decimal('0'))
        # No extra payment is applied in month 1 (before any loan has freed up EMI capacity).
        month1 = [item for item in result['items'] if item['month_number'] == 1]
        self.assertTrue(all(item['extra_payment'] == Decimal('0.00') for item in month1))
        self.assertGreater(result['months_remaining'], 0)

    def test_extra_payment_exceeding_capacity_rejected(self):
        with self.assertRaises(RepaymentPlanError):
            self._generate(extra_payment=Decimal('1000'))

    def test_no_eligible_loans_rejected(self):
        Loan.objects.filter(user=self.user).delete()
        with self.assertRaises(RepaymentPlanError):
            self._generate()

    def test_non_monthly_loans_excluded_with_reason(self):
        quarterly = self._make_loan(
            'Quarterly', rate='10', outstanding='500', emi='100', payment_frequency=Loan.PaymentFrequency.QUARTERLY
        )
        result = self._generate()
        self.assertTrue(any(x['loan_id'] == quarterly.id for x in result['excluded_loans']))
        self.assertFalse(any(item['loan_name'] == 'Quarterly' for item in result['items']))

    def test_emi_not_covering_interest_rejected(self):
        self._make_loan('Bad', rate='50', outstanding='100000', emi='100')
        with self.assertRaises(RepaymentPlanError):
            self._generate(extra_payment=Decimal('0'))

    def test_assumptions_are_always_present(self):
        result = self._generate()
        self.assertTrue(len(result['assumptions']) > 0)

    def test_plan_is_deterministic(self):
        first = self._generate()
        second = self._generate()
        self.assertEqual(first['items'], second['items'])
        self.assertEqual(first['months_remaining'], second['months_remaining'])


class RepaymentPlanAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)

        Loan.objects.create(
            user=self.user, loan_name='A', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('1200'), outstanding_principal=Decimal('1200'),
            annual_interest_rate=Decimal('12'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            payment_frequency=Loan.PaymentFrequency.MONTHLY, emi_amount=Decimal('200'),
            start_date=date(2026, 1, 1), maturity_date=date(2030, 1, 1),
        )
        self.generate_payload = {
            'strategy': 'AVALANCHE',
            'monthly_income': '1000',
            'essential_expenses': '400',
            'extra_payment': '100',
        }

    def test_generate_persists_plan_and_items(self):
        response = self.client.post(reverse('repayment-plan-generate'), self.generate_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(RepaymentPlan.objects.count(), 1)
        self.assertGreater(len(response.data['plan']['items']), 0)

    def test_generate_rejects_over_capacity_extra_payment(self):
        payload = {**self.generate_payload, 'extra_payment': '10000'}
        response = self.client.post(reverse('repayment-plan-generate'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_list_only_returns_own_plans(self):
        self.client.post(reverse('repayment-plan-generate'), self.generate_payload)
        self.client.force_authenticate(self.other_user)
        response = self.client.get(reverse('repayment-plan-list'))
        self.assertEqual(response.data['count'], 0)

    def test_detail_view_includes_items_and_assumptions(self):
        create_response = self.client.post(reverse('repayment-plan-generate'), self.generate_payload)
        plan_id = create_response.data['plan']['id']

        response = self.client.get(reverse('repayment-plan-detail', args=[plan_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertIn('assumptions', response.data)

    def test_cannot_view_other_users_plan(self):
        create_response = self.client.post(reverse('repayment-plan-generate'), self.generate_payload)
        plan_id = create_response.data['plan']['id']

        self.client.force_authenticate(self.other_user)
        response = self.client.get(reverse('repayment-plan-detail', args=[plan_id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse('repayment-plan-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
