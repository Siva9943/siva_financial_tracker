from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.loans.models import Loan, LoanPayment
from apps.transactions.models import Transaction
from services.financial_analysis_service import calculate_ratios, get_financial_analytics

from .dashboard import build_dashboard
from .date_ranges import resolve_range

User = get_user_model()


class DateRangeTests(TestCase):
    def test_current_month(self):
        bounds = resolve_range('CURRENT_MONTH', today=date(2026, 3, 19))
        self.assertEqual(bounds['start'], date(2026, 3, 1))
        self.assertEqual(bounds['end'], date(2026, 3, 19))
        self.assertEqual(bounds['previous_start'], date(2026, 2, 1))
        self.assertEqual(bounds['previous_end'], date(2026, 2, 19))

    def test_current_month_clamps_short_previous_month(self):
        # March 31 has no equivalent day in a 28-day February — relativedelta clamps it.
        bounds = resolve_range('CURRENT_MONTH', today=date(2026, 3, 31))
        self.assertEqual(bounds['previous_end'], date(2026, 2, 28))

    def test_previous_month(self):
        bounds = resolve_range('PREVIOUS_MONTH', today=date(2026, 3, 19))
        self.assertEqual(bounds['start'], date(2026, 2, 1))
        self.assertEqual(bounds['end'], date(2026, 2, 28))
        self.assertEqual(bounds['previous_start'], date(2026, 1, 1))
        self.assertEqual(bounds['previous_end'], date(2026, 1, 31))

    def test_current_year(self):
        bounds = resolve_range('CURRENT_YEAR', today=date(2026, 3, 19))
        self.assertEqual(bounds['start'], date(2026, 1, 1))
        self.assertEqual(bounds['end'], date(2026, 3, 19))
        self.assertEqual(bounds['previous_start'], date(2025, 1, 1))
        self.assertEqual(bounds['previous_end'], date(2025, 3, 19))

    def test_custom_range_previous_is_equal_length_trailing_window(self):
        bounds = resolve_range('CUSTOM', start=date(2026, 3, 1), end=date(2026, 3, 31))
        self.assertEqual(bounds['previous_start'], date(2026, 1, 29))
        self.assertEqual(bounds['previous_end'], date(2026, 2, 28))

    def test_custom_range_requires_dates(self):
        with self.assertRaises(ValueError):
            resolve_range('CUSTOM')

    def test_custom_range_rejects_end_before_start(self):
        with self.assertRaises(ValueError):
            resolve_range('CUSTOM', start=date(2026, 3, 31), end=date(2026, 3, 1))

    def test_unknown_range_rejected(self):
        with self.assertRaises(ValueError):
            resolve_range('MADE_UP')


class FinancialAnalyticsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('5000'), category='Salary', transaction_date=date(2026, 3, 5),
        )
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal('2000'), category='Food', transaction_date=date(2026, 3, 10),
        )
        self.loan = Loan.objects.create(
            user=self.user, loan_name='Personal Loan', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('10000'), outstanding_principal=Decimal('9200'),
            annual_interest_rate=Decimal('12'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            payment_frequency=Loan.PaymentFrequency.MONTHLY, emi_amount=Decimal('900'),
            start_date=date(2026, 1, 1), maturity_date=date(2030, 1, 1),
        )
        LoanPayment.objects.create(
            loan=self.loan, payment_date=date(2026, 3, 15), amount=Decimal('900'),
            principal_component=Decimal('800'), interest_component=Decimal('100'), remaining_principal=Decimal('9200'),
        )

    def test_calculate_ratios_guards_zero_income(self):
        ratios = calculate_ratios({'income': Decimal('0'), 'expenses': Decimal('0'), 'debt_payments': Decimal('0'), 'interest_paid': Decimal('0')})
        self.assertIsNone(ratios['savings_rate'])
        self.assertIsNone(ratios['debt_to_income'])
        self.assertIsNone(ratios['expense_ratio'])
        self.assertIsNone(ratios['interest_burden'])

    def test_calculate_ratios_known_values(self):
        ratios = calculate_ratios({'income': Decimal('5000'), 'expenses': Decimal('2000'), 'debt_payments': Decimal('900'), 'interest_paid': Decimal('100')})
        self.assertEqual(ratios['savings_rate'], 60.0)
        self.assertEqual(ratios['debt_to_income'], 18.0)
        self.assertEqual(ratios['expense_ratio'], 40.0)
        self.assertEqual(ratios['interest_burden'], 11.11)

    def test_get_financial_analytics_current_period_matches_fixture(self):
        result = get_financial_analytics(self.user, 'CUSTOM', start=date(2026, 3, 1), end=date(2026, 3, 31))
        self.assertEqual(result['metrics']['savings_rate']['current'], 60.0)
        self.assertEqual(result['metrics']['debt_to_income']['current'], 18.0)
        self.assertEqual(result['metrics']['expense_ratio']['current'], 40.0)
        self.assertEqual(result['metrics']['interest_burden']['current'], 11.11)

    def test_get_financial_analytics_previous_period_is_empty_and_change_is_none(self):
        result = get_financial_analytics(self.user, 'CUSTOM', start=date(2026, 3, 1), end=date(2026, 3, 31))
        for key in ('savings_rate', 'debt_to_income', 'expense_ratio', 'interest_burden'):
            self.assertIsNone(result['metrics'][key]['previous'])
            self.assertIsNone(result['metrics'][key]['change'])

    def test_historical_series_has_requested_length(self):
        result = get_financial_analytics(self.user, 'CURRENT_MONTH', history_periods=6, start=None, end=None)
        self.assertEqual(len(result['historical']), 6)

    def test_no_financial_health_score_field(self):
        result = get_financial_analytics(self.user, 'CUSTOM', start=date(2026, 3, 1), end=date(2026, 3, 31))
        self.assertNotIn('score', result)
        self.assertNotIn('health_score', result)


class DashboardAggregationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('5000'), category='Salary', transaction_date=date(2026, 3, 5),
        )
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal('2000'), category='Food', transaction_date=date(2026, 3, 10),
        )
        self.loan = Loan.objects.create(
            user=self.user, loan_name='Personal Loan', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('10000'), outstanding_principal=Decimal('9200'),
            annual_interest_rate=Decimal('12'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            payment_frequency=Loan.PaymentFrequency.MONTHLY, emi_amount=Decimal('900'),
            start_date=date(2026, 1, 1), maturity_date=date(2030, 1, 1),
        )
        LoanPayment.objects.create(
            loan=self.loan, payment_date=date(2026, 3, 15), amount=Decimal('900'),
            principal_component=Decimal('800'), interest_component=Decimal('100'), remaining_principal=Decimal('9200'),
        )

    def test_cards_match_fixture(self):
        result = build_dashboard(self.user, date(2026, 3, 1), date(2026, 3, 31))
        cards = result['cards']
        self.assertEqual(cards['total_income'], Decimal('5000.00'))
        self.assertEqual(cards['total_expenses'], Decimal('2000.00'))
        self.assertEqual(cards['savings'], Decimal('3000.00'))
        self.assertEqual(cards['total_debt'], Decimal('10000.00'))
        self.assertEqual(cards['outstanding_principal'], Decimal('9200.00'))
        self.assertEqual(cards['interest_paid'], Decimal('100.00'))
        self.assertEqual(cards['monthly_emi'], Decimal('900.00'))
        self.assertEqual(cards['available_balance'], Decimal('2100.00'))

    def test_expense_by_category_chart(self):
        result = build_dashboard(self.user, date(2026, 3, 1), date(2026, 3, 31))
        breakdown = result['charts']['expense_by_category']
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]['category'], 'Food')
        self.assertEqual(breakdown[0]['total'], Decimal('2000.00'))

    def test_loan_balance_chart(self):
        result = build_dashboard(self.user, date(2026, 3, 1), date(2026, 3, 31))
        self.assertEqual(result['charts']['loan_balance'], [{'loan_name': 'Personal Loan', 'outstanding_principal': Decimal('9200.00')}])

    def test_interest_vs_principal_chart(self):
        result = build_dashboard(self.user, date(2026, 3, 1), date(2026, 3, 31))
        self.assertEqual(result['charts']['interest_vs_principal'], {'interest': Decimal('100.00'), 'principal': Decimal('800.00')})

    def test_budget_usage_empty_when_no_budgets(self):
        result = build_dashboard(self.user, date(2026, 3, 1), date(2026, 3, 31))
        self.assertEqual(result['charts']['budget_usage']['categories'], [])

    def test_debt_payoff_projection_has_twelve_months_and_decreases(self):
        result = build_dashboard(self.user, date(2026, 3, 1), date(2026, 3, 31))
        projection = result['charts']['debt_payoff_projection']
        self.assertEqual(len(projection), 12)
        self.assertLessEqual(projection[0]['total_outstanding'], Decimal('9200.00'))
        balances = [row['total_outstanding'] for row in projection]
        self.assertEqual(balances, sorted(balances, reverse=True))

    def test_income_vs_expense_uses_daily_buckets_for_short_range(self):
        result = build_dashboard(self.user, date(2026, 3, 1), date(2026, 3, 31))
        series = result['charts']['income_vs_expense']
        self.assertEqual(len(series), 2)  # one bucket for the income day, one for the expense day


class DashboardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)

        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('1000'), category='Salary', transaction_date=date.today(),
        )
        Transaction.objects.create(
            user=self.other_user, transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('999999'), category='Salary', transaction_date=date.today(),
        )

    def test_dashboard_default_range(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cards']['total_income'], Decimal('1000.00'))

    def test_dashboard_isolates_users(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.data['cards']['total_income'], Decimal('1000.00'))

    def test_dashboard_rejects_unknown_range(self):
        response = self.client.get(reverse('dashboard'), {'range': 'MADE_UP'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_custom_range_requires_dates(self):
        response = self.client.get(reverse('dashboard'), {'range': 'CUSTOM'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_custom_range_with_dates(self):
        response = self.client.get(reverse('dashboard'), {'range': 'CUSTOM', 'start': '2020-01-01', 'end': '2020-01-31'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cards']['total_income'], Decimal('0.00'))

    def test_dashboard_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_analytics_default_range(self):
        response = self.client.get(reverse('analytics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metrics', response.data)
        self.assertIn('historical', response.data)

    def test_analytics_rejects_unknown_range(self):
        response = self.client.get(reverse('analytics'), {'range': 'MADE_UP'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analytics_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse('analytics'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
