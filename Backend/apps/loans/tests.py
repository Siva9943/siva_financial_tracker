from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.transactions.models import Transaction
from services.emi_service import EMICalculationService
from services.interest_service import InterestCalculationService
from services.loan_payment_service import LoanPaymentError, record_loan_payment
from services.loan_priority_service import rank_loans

from .models import Loan, LoanPayment

User = get_user_model()


class LoanCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.list_url = reverse('loan-list')

    def _payload(self, **overrides):
        payload = {
            'loan_name': 'Home Loan',
            'loan_type': Loan.LoanType.HOME,
            'lender': 'ABC Bank',
            'original_principal': '2000000.00',
            'annual_interest_rate': '8.500',
            'interest_calculation_method': Loan.InterestMethod.EMI_AMORTIZATION,
            'emi_amount': '17500.00',
            'payment_frequency': Loan.PaymentFrequency.MONTHLY,
            'start_date': '2026-01-01',
            'maturity_date': '2046-01-01',
        }
        payload.update(overrides)
        return payload

    def test_create_loan_defaults_outstanding_to_original(self):
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['outstanding_principal'], '2000000.00')
        self.assertEqual(response.data['next_due_date'], '2026-02-01')
        self.assertEqual(response.data['status'], 'ACTIVE')

    def test_gold_loan_type_accepted(self):
        response = self.client.post(self.list_url, self._payload(loan_type=Loan.LoanType.GOLD_LOAN, loan_name='Gold Loan'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['loan_type'], 'GOLD_LOAN')

    def test_maturity_must_be_after_start(self):
        response = self.client.post(self.list_url, self._payload(maturity_date='2025-01-01'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_original_principal_must_be_positive(self):
        response = self.client.post(self.list_url, self._payload(original_principal='0'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_interest_rate_cannot_be_negative(self):
        response = self.client.post(self.list_url, self._payload(annual_interest_rate='-1'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_emi_amount_must_be_positive_when_given(self):
        response = self.client.post(self.list_url, self._payload(emi_amount='0'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outstanding_cannot_exceed_original(self):
        response = self.client.post(
            self.list_url, self._payload(outstanding_principal='2500000.00')
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_explicit_outstanding_principal_is_respected(self):
        response = self.client.post(self.list_url, self._payload(outstanding_principal='1500000.00'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['outstanding_principal'], '1500000.00')

    def test_list_only_returns_own_loans(self):
        self.client.post(self.list_url, self._payload())
        other_loan = Loan.objects.create(
            user=self.other_user,
            loan_name='Car Loan',
            loan_type=Loan.LoanType.VEHICLE,
            original_principal=Decimal('500000'),
            outstanding_principal=Decimal('500000'),
            annual_interest_rate=Decimal('9.5'),
            interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1),
            maturity_date=date(2031, 1, 1),
        )

        response = self.client.get(self.list_url)
        returned_ids = [item['id'] for item in response.data['results']]
        self.assertNotIn(other_loan.id, returned_ids)

    def test_cannot_access_other_users_loan(self):
        other_loan = Loan.objects.create(
            user=self.other_user,
            loan_name='Car Loan',
            loan_type=Loan.LoanType.VEHICLE,
            original_principal=Decimal('500000'),
            outstanding_principal=Decimal('500000'),
            annual_interest_rate=Decimal('9.5'),
            interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1),
            maturity_date=date(2031, 1, 1),
        )
        detail_url = reverse('loan-detail', args=[other_loan.id])
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_update_and_delete_own_loan(self):
        create_response = self.client.post(self.list_url, self._payload())
        loan_id = create_response.data['id']
        detail_url = reverse('loan-detail', args=[loan_id])

        update_response = self.client.patch(detail_url, {'status': 'PAUSED'})
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['status'], 'PAUSED')

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Loan.objects.count(), 0)

    def test_filter_by_status_and_type(self):
        self.client.post(self.list_url, self._payload(loan_name='Home', loan_type=Loan.LoanType.HOME))
        self.client.post(self.list_url, self._payload(loan_name='Car', loan_type=Loan.LoanType.VEHICLE))

        response = self.client.get(self.list_url, {'loan_type': 'VEHICLE'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['loan_name'], 'Car')

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summary_endpoint(self):
        self.client.post(self.list_url, self._payload(loan_name='Home', original_principal='2000000'))
        self.client.post(
            self.list_url,
            self._payload(loan_name='Car', original_principal='500000', emi_amount='9000', status='COMPLETED'),
        )

        response = self.client.get(reverse('loan-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data['total_original_principal'])), Decimal('2500000'))
        self.assertEqual(response.data['active_loan_count'], 1)
        self.assertEqual(response.data['completed_loan_count'], 1)
        self.assertEqual(Decimal(str(response.data['monthly_debt_payment'])), Decimal('17500'))


class LoanModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def test_maturity_date_constraint_enforced_at_db_level(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Loan.objects.create(
                user=self.user,
                loan_name='Bad Loan',
                loan_type=Loan.LoanType.PERSONAL,
                original_principal=Decimal('1000'),
                outstanding_principal=Decimal('1000'),
                annual_interest_rate=Decimal('5'),
                interest_calculation_method=Loan.InterestMethod.FLAT_RATE,
                start_date=date(2026, 1, 1),
                maturity_date=date(2025, 1, 1),
            )

    def test_next_due_date_advances_by_payment_frequency(self):
        loan = Loan.objects.create(
            user=self.user,
            loan_name='Quarterly Loan',
            loan_type=Loan.LoanType.BUSINESS,
            original_principal=Decimal('10000'),
            outstanding_principal=Decimal('10000'),
            annual_interest_rate=Decimal('10'),
            interest_calculation_method=Loan.InterestMethod.FLAT_RATE,
            payment_frequency=Loan.PaymentFrequency.QUARTERLY,
            start_date=date(2026, 1, 31),
            maturity_date=date(2030, 1, 31),
        )
        self.assertEqual(loan.next_due_date, date(2026, 4, 30))


class InterestCalculationServiceTests(TestCase):
    def test_daily_interest(self):
        # 100000 x 12% / 365 = 32.876... -> 32.88
        result = InterestCalculationService.daily_interest(Decimal('100000'), Decimal('12'))
        self.assertEqual(result, Decimal('32.88'))

    def test_monthly_interest(self):
        result = InterestCalculationService.monthly_interest(Decimal('100000'), Decimal('12'))
        self.assertEqual(result, Decimal('1000.00'))

    def test_flat_rate_total_interest(self):
        result = InterestCalculationService.flat_rate_total_interest(Decimal('100000'), Decimal('12'), Decimal('1'))
        self.assertEqual(result, Decimal('12000.00'))

    def test_interest_for_days_computed_directly_not_via_rounded_daily_rate(self):
        # 50000 x 9% / 365 x 30 = 369.863... -> 369.86 (computed in one step, not
        # daily_interest()'s already-rounded 12.33 x 30 = 369.90, which would drift).
        for_30_days = InterestCalculationService.interest_for_days(Decimal('50000'), Decimal('9'), 30)
        self.assertEqual(for_30_days, Decimal('369.86'))


class EMICalculationServiceTests(TestCase):
    def test_classic_example_100000_at_12_percent_for_12_months(self):
        emi = EMICalculationService.calculate_emi(Decimal('100000'), Decimal('12'), 12, 12)
        self.assertEqual(emi, Decimal('8884.88'))

    def test_zero_interest_emi_is_simple_division(self):
        emi = EMICalculationService.calculate_emi(Decimal('12000'), Decimal('0'), 12, 12)
        self.assertEqual(emi, Decimal('1000.00'))

    def test_zero_tenure_raises(self):
        with self.assertRaises(ValueError):
            EMICalculationService.calculate_emi(Decimal('1000'), Decimal('10'), 0, 12)

    def test_large_principal_no_precision_loss(self):
        # A large principal should not introduce float-style rounding drift.
        emi = EMICalculationService.calculate_emi(Decimal('50000000'), Decimal('9.5'), 240, 12)
        self.assertIsInstance(emi, Decimal)
        self.assertGreater(emi, Decimal('0'))


class AmortizationScheduleTests(TestCase):
    def test_emi_amortization_schedule_invariants(self):
        schedule = EMICalculationService.generate_schedule(
            principal=Decimal('100000'),
            annual_rate=Decimal('12'),
            tenure_periods=12,
            periods_per_year=12,
            start_date=date(2026, 1, 1),
            frequency='MONTHLY',
            method='EMI_AMORTIZATION',
        )
        self.assertEqual(len(schedule), 12)
        self.assertEqual(schedule[-1]['closing_balance'], Decimal('0.00'))
        total_principal = sum((row['principal'] for row in schedule), Decimal('0.00'))
        self.assertEqual(total_principal, Decimal('100000.00'))
        # Reducing balance: interest strictly decreases period over period.
        interests = [row['interest'] for row in schedule]
        self.assertEqual(interests, sorted(interests, reverse=True))

    def test_flat_rate_schedule_has_constant_interest(self):
        schedule = EMICalculationService.generate_schedule(
            principal=Decimal('100000'),
            annual_rate=Decimal('12'),
            tenure_periods=12,
            periods_per_year=12,
            start_date=date(2026, 1, 1),
            frequency='MONTHLY',
            method='FLAT_RATE',
        )
        self.assertEqual(len(schedule), 12)
        self.assertEqual(schedule[-1]['closing_balance'], Decimal('0.00'))
        interests = {row['interest'] for row in schedule[:-1]}
        self.assertEqual(len(interests), 1)  # constant interest every period except possible last-period true-up
        total_principal = sum((row['principal'] for row in schedule), Decimal('0.00'))
        self.assertEqual(total_principal, Decimal('100000.00'))

    def test_daily_reducing_balance_handles_different_month_lengths(self):
        schedule = EMICalculationService.generate_schedule(
            principal=Decimal('10000'),
            annual_rate=Decimal('12'),
            tenure_periods=3,
            periods_per_year=12,
            start_date=date(2026, 1, 1),
            frequency='MONTHLY',
            method='DAILY_REDUCING_BALANCE',
        )
        # Jan (31 days) accrues more interest than Feb (28 days, 2026 is not a leap year) on a similar balance.
        self.assertEqual(schedule[0]['date'], date(2026, 2, 1))
        self.assertEqual(schedule[1]['date'], date(2026, 3, 1))
        self.assertGreater(schedule[0]['interest'], schedule[1]['interest'])
        self.assertEqual(schedule[-1]['closing_balance'], Decimal('0.00'))

    def test_monthly_reducing_balance_ignores_loan_payment_frequency_for_compounding(self):
        # A quarterly-paid loan under MONTHLY_REDUCING_BALANCE still compounds monthly.
        schedule = EMICalculationService.generate_schedule(
            principal=Decimal('100000'),
            annual_rate=Decimal('12'),
            tenure_periods=4,
            periods_per_year=4,
            start_date=date(2026, 1, 1),
            frequency='QUARTERLY',
            method='MONTHLY_REDUCING_BALANCE',
        )
        emi = EMICalculationService.calculate_emi(Decimal('100000'), Decimal('12'), 4, 12)
        self.assertEqual(schedule[0]['payment'], emi)

    def test_unknown_method_raises(self):
        with self.assertRaises(ValueError):
            EMICalculationService.generate_schedule(
                principal=Decimal('1000'),
                annual_rate=Decimal('5'),
                tenure_periods=12,
                periods_per_year=12,
                start_date=date(2026, 1, 1),
                frequency='MONTHLY',
                method='UNKNOWN',
            )


class LoanCalculatorAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.client.force_authenticate(self.user)

    def test_loan_calculator_returns_schedule(self):
        response = self.client.post(
            reverse('loan-calculator'),
            {
                'original_principal': '100000',
                'annual_interest_rate': '12',
                'interest_calculation_method': 'EMI_AMORTIZATION',
                'payment_frequency': 'MONTHLY',
                'start_date': '2026-01-01',
                'maturity_date': '2027-01-01',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['emi'], Decimal('8884.88'))
        self.assertEqual(len(response.data['schedule']), 12)

    def test_loan_calculator_rejects_invalid_dates(self):
        response = self.client.post(
            reverse('loan-calculator'),
            {
                'original_principal': '100000',
                'annual_interest_rate': '12',
                'interest_calculation_method': 'EMI_AMORTIZATION',
                'start_date': '2027-01-01',
                'maturity_date': '2026-01-01',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_loan_amortization_endpoint(self):
        loan_response = self.client.post(
            reverse('loan-list'),
            {
                'loan_name': 'Home Loan',
                'loan_type': 'HOME',
                'original_principal': '100000',
                'annual_interest_rate': '12',
                'interest_calculation_method': 'EMI_AMORTIZATION',
                'start_date': '2026-01-01',
                'maturity_date': '2027-01-01',
            },
        )
        loan_id = loan_response.data['id']

        response = self.client.get(reverse('loan-amortization', args=[loan_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['emi'], Decimal('8884.88'))
        self.assertEqual(response.data['tenure_periods'], 12)
        self.assertEqual(len(response.data['schedule']), 12)

    def test_amortization_uses_stored_emi_when_present(self):
        loan_response = self.client.post(
            reverse('loan-list'),
            {
                'loan_name': 'Custom EMI Loan',
                'loan_type': 'PERSONAL',
                'original_principal': '100000',
                'annual_interest_rate': '12',
                'interest_calculation_method': 'EMI_AMORTIZATION',
                'emi_amount': '10000',
                'start_date': '2026-01-01',
                'maturity_date': '2027-01-01',
            },
        )
        loan_id = loan_response.data['id']

        response = self.client.get(reverse('loan-amortization', args=[loan_id]))
        self.assertEqual(response.data['schedule'][0]['payment'], Decimal('10000.00'))


class LoanPaymentServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def _make_loan(self, **overrides):
        defaults = dict(
            user=self.user,
            loan_name='Home Loan',
            loan_type=Loan.LoanType.HOME,
            original_principal=Decimal('100000'),
            annual_interest_rate=Decimal('12'),
            interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            payment_frequency=Loan.PaymentFrequency.MONTHLY,
            start_date=date(2026, 1, 1),
            maturity_date=date(2027, 1, 1),
        )
        defaults.update(overrides)
        return Loan.objects.create(**defaults)

    def test_first_payment_matches_amortization_schedule(self):
        loan = self._make_loan()
        payment = record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('8884.88'))

        self.assertEqual(payment.interest_component, Decimal('1000.00'))
        self.assertEqual(payment.principal_component, Decimal('7884.88'))
        self.assertEqual(payment.remaining_principal, Decimal('92115.12'))
        self.assertEqual(payment.extra_payment, Decimal('0.00'))

        loan.refresh_from_db()
        self.assertEqual(loan.outstanding_principal, Decimal('92115.12'))
        self.assertEqual(loan.next_due_date, date(2026, 3, 1))
        self.assertEqual(loan.status, Loan.Status.ACTIVE)

    def test_extra_payment_is_tracked_and_reduces_balance_further(self):
        loan = self._make_loan()
        payment = record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('10000.00'))

        self.assertEqual(payment.interest_component, Decimal('1000.00'))
        self.assertEqual(payment.principal_component, Decimal('9000.00'))
        self.assertEqual(payment.extra_payment, Decimal('1115.12'))  # 9000 - scheduled 7884.88
        self.assertEqual(payment.remaining_principal, Decimal('91000.00'))

    def test_partial_payment_covers_only_interest(self):
        loan = self._make_loan()
        payment = record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('500.00'))

        self.assertEqual(payment.interest_component, Decimal('500.00'))
        self.assertEqual(payment.principal_component, Decimal('0.00'))
        self.assertEqual(payment.remaining_principal, Decimal('100000.00'))
        loan.refresh_from_db()
        self.assertEqual(loan.outstanding_principal, Decimal('100000.00'))

    def test_late_fee_auto_applied_when_overdue_and_resolves_status(self):
        loan = self._make_loan(late_fee=Decimal('50.00'), status=Loan.Status.OVERDUE)
        loan.next_due_date = date(2026, 2, 1)
        loan.save(update_fields=['next_due_date'])

        payment = record_loan_payment(loan, payment_date=date(2026, 2, 15), amount=Decimal('8884.88'))

        self.assertEqual(payment.late_fee, Decimal('50.00'))
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.ACTIVE)

    def test_explicit_late_fee_overrides_default(self):
        loan = self._make_loan(late_fee=Decimal('50.00'))
        payment = record_loan_payment(
            loan, payment_date=date(2026, 2, 1), amount=Decimal('8884.88'), late_fee=Decimal('25.00')
        )
        self.assertEqual(payment.late_fee, Decimal('25.00'))

    def test_late_fee_cannot_exceed_amount(self):
        loan = self._make_loan()
        with self.assertRaises(LoanPaymentError):
            record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('10.00'), late_fee=Decimal('50.00'))

    def test_payment_exceeding_full_payoff_rejected(self):
        loan = self._make_loan()
        with self.assertRaises(LoanPaymentError):
            record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('999999.00'))

    def test_final_payment_completes_loan(self):
        loan = self._make_loan(original_principal=Decimal('1000'), outstanding_principal=Decimal('1000'))
        payment = record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('1010.00'))

        self.assertEqual(payment.remaining_principal, Decimal('0.00'))
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.COMPLETED)
        self.assertEqual(loan.outstanding_principal, Decimal('0.00'))
        self.assertIsNone(loan.next_due_date)

    def test_cannot_pay_a_completed_loan(self):
        loan = self._make_loan(status=Loan.Status.COMPLETED)
        with self.assertRaises(LoanPaymentError):
            record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('100.00'))

    def test_cannot_pay_a_paused_loan(self):
        loan = self._make_loan(status=Loan.Status.PAUSED)
        with self.assertRaises(LoanPaymentError):
            record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('100.00'))

    def test_linked_transaction_created(self):
        loan = self._make_loan()
        payment = record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('8884.88'))

        self.assertIsNotNone(payment.transaction)
        self.assertEqual(payment.transaction.transaction_type, Transaction.TransactionType.LOAN_PAYMENT)
        self.assertEqual(payment.transaction.amount, Decimal('8884.88'))
        self.assertEqual(payment.transaction.user, loan.user)

    def test_second_payment_uses_reduced_balance(self):
        loan = self._make_loan()
        record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('8884.88'))
        loan.refresh_from_db()

        second = record_loan_payment(loan, payment_date=date(2026, 3, 1), amount=Decimal('8884.88'))
        # Interest on period 2 should be based on the reduced balance (92115.12), matching the schedule.
        self.assertEqual(second.interest_component, Decimal('921.15'))

    def test_flat_rate_payment_has_constant_interest_regardless_of_balance(self):
        loan = self._make_loan(interest_calculation_method=Loan.InterestMethod.FLAT_RATE)
        first = record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('9000.00'))
        loan.refresh_from_db()
        second = record_loan_payment(loan, payment_date=date(2026, 3, 1), amount=Decimal('9000.00'))

        # Flat-rate interest is constant per period, unaffected by the extra principal paid in period 1.
        self.assertEqual(first.interest_component, second.interest_component)

    def test_daily_reducing_balance_uses_actual_days_elapsed(self):
        loan = self._make_loan(interest_calculation_method=Loan.InterestMethod.DAILY_REDUCING_BALANCE)
        # January has 31 days; February (2026, non-leap) has 28.
        first = record_loan_payment(loan, payment_date=date(2026, 2, 1), amount=Decimal('9000.00'))
        loan.refresh_from_db()
        second = record_loan_payment(loan, payment_date=date(2026, 3, 1), amount=Decimal('9000.00'))

        self.assertGreater(first.interest_component, second.interest_component)


class LoanPaymentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)

        self.loan = Loan.objects.create(
            user=self.user,
            loan_name='Home Loan',
            loan_type=Loan.LoanType.HOME,
            original_principal=Decimal('100000'),
            annual_interest_rate=Decimal('12'),
            interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1),
            maturity_date=date(2027, 1, 1),
        )
        self.payments_url = reverse('loan-payments', args=[self.loan.id])

    def test_record_payment_via_api(self):
        response = self.client.post(self.payments_url, {'payment_date': '2026-02-01', 'amount': '8884.88'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['payment']['interest_component'], '1000.00')
        self.assertEqual(response.data['loan']['outstanding_principal'], '92115.12')
        self.assertEqual(LoanPayment.objects.count(), 1)

    def test_list_payments_via_api(self):
        self.client.post(self.payments_url, {'payment_date': '2026-02-01', 'amount': '8884.88'})
        response = self.client.get(self.payments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_invalid_payment_returns_400_with_message(self):
        response = self.client.post(self.payments_url, {'payment_date': '2026-02-01', 'amount': '999999.00'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Maximum payoff amount', response.data['message'])

    def test_cannot_record_payment_for_other_users_loan(self):
        other_loan = Loan.objects.create(
            user=self.other_user,
            loan_name='Car Loan',
            loan_type=Loan.LoanType.VEHICLE,
            original_principal=Decimal('50000'),
            outstanding_principal=Decimal('50000'),
            annual_interest_rate=Decimal('9'),
            interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1),
            maturity_date=date(2028, 1, 1),
        )
        url = reverse('loan-payments', args=[other_loan.id])
        response = self.client.post(url, {'payment_date': '2026-02-01', 'amount': '100'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_negative_amount_rejected_by_serializer(self):
        response = self.client.post(self.payments_url, {'payment_date': '2026-02-01', 'amount': '-100'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoanPriorityServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.loan_a = self._make_loan('A', rate='18', outstanding='50000')
        self.loan_b = self._make_loan('B', rate='10', outstanding='20000')
        self.loan_c = self._make_loan('C', rate='14', outstanding='100000')

    def _make_loan(self, name, *, rate, outstanding, **overrides):
        defaults = dict(
            user=self.user,
            loan_name=name,
            loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal(outstanding),
            outstanding_principal=Decimal(outstanding),
            annual_interest_rate=Decimal(rate),
            interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1),
            maturity_date=date(2031, 1, 1),
        )
        defaults.update(overrides)
        return Loan.objects.create(**defaults)

    def test_avalanche_orders_by_interest_rate_descending(self):
        results = rank_loans(Loan.objects.filter(user=self.user), 'AVALANCHE')
        self.assertEqual([r['loan_name'] for r in results], ['A', 'C', 'B'])
        self.assertEqual(results[0]['rank'], 1)
        self.assertEqual(results[0]['priority_level'], 'High')
        self.assertIn('annual interest rate', results[0]['reason'])

    def test_snowball_orders_by_outstanding_balance_ascending(self):
        results = rank_loans(Loan.objects.filter(user=self.user), 'SNOWBALL')
        self.assertEqual([r['loan_name'] for r in results], ['B', 'A', 'C'])
        self.assertIn('outstanding balance', results[0]['reason'])

    def test_custom_orders_by_priority_order_then_unset_last(self):
        self.loan_c.priority_order = 1
        self.loan_c.save(update_fields=['priority_order'])
        self.loan_a.priority_order = 2
        self.loan_a.save(update_fields=['priority_order'])
        # loan_b has no priority_order set — should sort last.

        results = rank_loans(Loan.objects.filter(user=self.user), 'CUSTOM')
        self.assertEqual([r['loan_name'] for r in results], ['C', 'A', 'B'])

    def test_priority_levels_bucket_by_rank(self):
        results = rank_loans(Loan.objects.filter(user=self.user), 'AVALANCHE')
        levels = [r['priority_level'] for r in results]
        self.assertEqual(levels, ['High', 'Medium', 'Low'])

    def test_single_loan_is_always_high_priority(self):
        results = rank_loans([self.loan_a], 'AVALANCHE')
        self.assertEqual(results[0]['priority_level'], 'High')

    def test_empty_loan_list_returns_empty(self):
        self.assertEqual(rank_loans([], 'AVALANCHE'), [])

    def test_unknown_strategy_raises(self):
        with self.assertRaises(ValueError):
            rank_loans(Loan.objects.filter(user=self.user), 'MADE_UP')

    def test_ranking_is_deterministic(self):
        first = rank_loans(Loan.objects.filter(user=self.user), 'AVALANCHE')
        second = rank_loans(Loan.objects.filter(user=self.user), 'AVALANCHE')
        self.assertEqual(first, second)


class LoanPriorityAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)

        self.loan_a = Loan.objects.create(
            user=self.user, loan_name='A', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('50000'), outstanding_principal=Decimal('50000'),
            annual_interest_rate=Decimal('18'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2031, 1, 1),
        )
        self.loan_b = Loan.objects.create(
            user=self.user, loan_name='B', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('20000'), outstanding_principal=Decimal('20000'),
            annual_interest_rate=Decimal('10'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2031, 1, 1),
        )
        self.completed_loan = Loan.objects.create(
            user=self.user, loan_name='Paid Off', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('5000'), outstanding_principal=Decimal('0'),
            annual_interest_rate=Decimal('99'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2031, 1, 1), status=Loan.Status.COMPLETED,
        )

    def test_priority_endpoint_defaults_to_avalanche(self):
        response = self.client.get(reverse('loan-priority'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['strategy'], 'AVALANCHE')
        names = [r['loan_name'] for r in response.data['results']]
        self.assertEqual(names, ['A', 'B'])  # completed loan excluded despite its high rate

    def test_priority_endpoint_snowball(self):
        response = self.client.get(reverse('loan-priority'), {'strategy': 'snowball'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([r['loan_name'] for r in response.data['results']], ['B', 'A'])

    def test_priority_endpoint_rejects_unknown_strategy(self):
        response = self.client.get(reverse('loan-priority'), {'strategy': 'MADE_UP'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_priority_only_includes_own_loans(self):
        Loan.objects.create(
            user=self.other_user, loan_name='Other', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('1000'), outstanding_principal=Decimal('1000'),
            annual_interest_rate=Decimal('50'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2031, 1, 1),
        )
        response = self.client.get(reverse('loan-priority'))
        names = [r['loan_name'] for r in response.data['results']]
        self.assertNotIn('Other', names)

    def test_reorder_sets_priority_order_sequentially(self):
        response = self.client.post(reverse('loan-reorder'), {'loan_ids': [self.loan_b.id, self.loan_a.id]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.loan_a.refresh_from_db()
        self.loan_b.refresh_from_db()
        self.assertEqual(self.loan_b.priority_order, 1)
        self.assertEqual(self.loan_a.priority_order, 2)

        custom_response = self.client.get(reverse('loan-priority'), {'strategy': 'custom'})
        self.assertEqual([r['loan_name'] for r in custom_response.data['results']], ['B', 'A'])

    def test_reorder_rejects_unknown_loan_id(self):
        response = self.client.post(reverse('loan-reorder'), {'loan_ids': [999999]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reorder_rejects_other_users_loan_id(self):
        other_loan = Loan.objects.create(
            user=self.other_user, loan_name='Other', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('1000'), outstanding_principal=Decimal('1000'),
            annual_interest_rate=Decimal('50'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2031, 1, 1),
        )
        response = self.client.post(reverse('loan-reorder'), {'loan_ids': [other_loan.id]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoanSimulatorTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.url = reverse('loan-simulator')

    def _ad_hoc_payload(self, **overrides):
        payload = {
            'original_principal': '100000',
            'annual_interest_rate': '12',
            'interest_calculation_method': 'EMI_AMORTIZATION',
            'payment_frequency': 'MONTHLY',
            'start_date': '2026-01-01',
            'maturity_date': '2027-01-01',
        }
        payload.update(overrides)
        return payload

    def test_default_scenarios_are_the_skill_defaults(self):
        response = self.client.post(self.url, self._ad_hoc_payload())
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        amounts = [Decimal(str(s['extra_payment'])) for s in response.data['scenarios']]
        self.assertEqual(amounts, [Decimal('0'), Decimal('1000'), Decimal('2000'), Decimal('5000'), Decimal('10000')])

    def test_extra_payment_shortens_payoff_and_saves_interest(self):
        response = self.client.post(self.url, self._ad_hoc_payload(extra_payment_scenarios=['0', '2000']))
        baseline = response.data['baseline']
        scenarios = {Decimal(str(s['extra_payment'])): s for s in response.data['scenarios']}

        zero_scenario = scenarios[Decimal('0')]
        extra_scenario = scenarios[Decimal('2000')]

        self.assertEqual(zero_scenario['months_to_payoff'], baseline['months_to_payoff'])
        self.assertEqual(zero_scenario['months_saved'], 0)
        self.assertEqual(zero_scenario['interest_saved'], Decimal('0.00'))

        self.assertLess(extra_scenario['months_to_payoff'], baseline['months_to_payoff'])
        self.assertGreater(extra_scenario['months_saved'], 0)
        self.assertGreater(Decimal(str(extra_scenario['interest_saved'])), Decimal('0.00'))

    def test_savings_increase_monotonically_with_extra_payment(self):
        response = self.client.post(self.url, self._ad_hoc_payload())
        scenarios = sorted(response.data['scenarios'], key=lambda s: Decimal(str(s['extra_payment'])))
        interest_saved = [Decimal(str(s['interest_saved'])) for s in scenarios]
        months_saved = [s['months_saved'] for s in scenarios]

        self.assertEqual(interest_saved, sorted(interest_saved))
        self.assertEqual(months_saved, sorted(months_saved))

    def test_flat_rate_and_daily_reducing_balance_also_benefit_from_extra_payment(self):
        for method in ('FLAT_RATE', 'DAILY_REDUCING_BALANCE'):
            response = self.client.post(
                self.url, self._ad_hoc_payload(interest_calculation_method=method, extra_payment_scenarios=['0', '2000'])
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            scenarios = {Decimal(str(s['extra_payment'])): s for s in response.data['scenarios']}
            self.assertGreater(scenarios[Decimal('2000')]['months_saved'], 0, method)
            self.assertGreater(Decimal(str(scenarios[Decimal('2000')]['interest_saved'])), Decimal('0.00'), method)

    def test_missing_fields_without_loan_id_rejected(self):
        response = self.client.post(self.url, {'annual_interest_rate': '12'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_simulate_existing_loan_by_id(self):
        loan = Loan.objects.create(
            user=self.user, loan_name='Home Loan', loan_type=Loan.LoanType.HOME,
            original_principal=Decimal('100000'), outstanding_principal=Decimal('100000'),
            annual_interest_rate=Decimal('12'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            payment_frequency=Loan.PaymentFrequency.MONTHLY,
            start_date=date(2026, 1, 1), maturity_date=date(2036, 1, 1),
        )
        response = self.client.post(self.url, {'loan_id': loan.id, 'extra_payment_scenarios': ['0', '2000']})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertGreater(response.data['baseline']['months_to_payoff'], 0)

    def test_simulate_other_users_loan_returns_404(self):
        other_loan = Loan.objects.create(
            user=self.other_user, loan_name='Car Loan', loan_type=Loan.LoanType.VEHICLE,
            original_principal=Decimal('50000'), outstanding_principal=Decimal('50000'),
            annual_interest_rate=Decimal('9'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2028, 1, 1),
        )
        response = self.client.post(self.url, {'loan_id': other_loan.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_simulate_matured_loan_rejected(self):
        loan = Loan.objects.create(
            user=self.user, loan_name='Old Loan', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('1000'), outstanding_principal=Decimal('1000'),
            annual_interest_rate=Decimal('5'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2020, 1, 1), maturity_date=date(2021, 1, 1),
        )
        response = self.client.post(self.url, {'loan_id': loan.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_extra_payment_matches_amortization_endpoint(self):
        loan = Loan.objects.create(
            user=self.user, loan_name='Home Loan', loan_type=Loan.LoanType.HOME,
            original_principal=Decimal('100000'), outstanding_principal=Decimal('100000'),
            annual_interest_rate=Decimal('12'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            payment_frequency=Loan.PaymentFrequency.MONTHLY,
            start_date=date(2026, 1, 1), maturity_date=date(2027, 1, 1),
        )
        amortization = self.client.get(reverse('loan-amortization', args=[loan.id]))
        simulation = self.client.post(
            self.url,
            self._ad_hoc_payload(
                original_principal='100000', start_date='2026-01-01', maturity_date='2027-01-01',
                extra_payment_scenarios=['0'],
            ),
        )
        self.assertEqual(simulation.data['baseline']['emi'], amortization.data['emi'])
        self.assertEqual(simulation.data['baseline']['total_interest'], amortization.data['total_interest'])
