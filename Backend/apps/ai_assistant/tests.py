import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.budgets.models import Budget
from apps.loans.models import Loan
from apps.transactions.models import Transaction

from .models import ChatMessage
from .tools import build_financial_tools

User = get_user_model()


class FinancialToolsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.tools = {t.name: t for t in build_financial_tools(self.user)}

    def test_no_tool_exposes_a_user_argument(self):
        # The LLM must never be able to choose or override whose data a tool reads.
        for name, tool_obj in self.tools.items():
            self.assertNotIn('user', tool_obj.args, f'{name} exposes a user argument')
            self.assertNotIn('user_id', tool_obj.args, f'{name} exposes a user_id argument')

    def test_get_monthly_income(self):
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('5000'), category='Salary', transaction_date=date(2026, 3, 5),
        )
        Transaction.objects.create(
            user=self.other_user, transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal('999999'), category='Salary', transaction_date=date(2026, 3, 5),
        )
        result = json.loads(self.tools['get_monthly_income'].invoke({'month': 3, 'year': 2026}))
        self.assertEqual(result['total_income'], '5000.00')

    def test_get_monthly_expenses(self):
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal('1200'), category='Food', transaction_date=date(2026, 3, 10),
        )
        result = json.loads(self.tools['get_monthly_expenses'].invoke({'month': 3, 'year': 2026}))
        self.assertEqual(result['total_expenses'], '1200.00')

    def test_get_expense_by_category(self):
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal('1200'), category='Food', transaction_date=date(2026, 3, 10),
        )
        result = json.loads(self.tools['get_expense_by_category'].invoke({'month': 3, 'year': 2026}))
        self.assertEqual(result['breakdown'][0]['category'], 'Food')

    def test_get_active_loans_excludes_other_users_and_completed(self):
        Loan.objects.create(
            user=self.user, loan_name='Home Loan', loan_type=Loan.LoanType.HOME,
            original_principal=Decimal('100000'), outstanding_principal=Decimal('90000'),
            annual_interest_rate=Decimal('10'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2030, 1, 1),
        )
        Loan.objects.create(
            user=self.user, loan_name='Paid Off', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('5000'), outstanding_principal=Decimal('0'),
            annual_interest_rate=Decimal('5'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2027, 1, 1), status=Loan.Status.COMPLETED,
        )
        Loan.objects.create(
            user=self.other_user, loan_name='Other Loan', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('1000'), outstanding_principal=Decimal('1000'),
            annual_interest_rate=Decimal('9'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2028, 1, 1),
        )
        result = json.loads(self.tools['get_active_loans'].invoke({}))
        names = [loan['loan_name'] for loan in result]
        self.assertEqual(names, ['Home Loan'])

    def test_get_loan_details_found_and_not_found(self):
        Loan.objects.create(
            user=self.user, loan_name='Home Loan', loan_type=Loan.LoanType.HOME,
            original_principal=Decimal('100000'), outstanding_principal=Decimal('90000'),
            annual_interest_rate=Decimal('10'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2030, 1, 1),
        )
        found = json.loads(self.tools['get_loan_details'].invoke({'loan_name': 'home'}))
        self.assertEqual(found['loan_name'], 'Home Loan')

        missing = json.loads(self.tools['get_loan_details'].invoke({'loan_name': 'nonexistent'}))
        self.assertIn('error', missing)

    def test_get_loan_details_cannot_see_other_users_loan(self):
        Loan.objects.create(
            user=self.other_user, loan_name='Secret Loan', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('1000'), outstanding_principal=Decimal('1000'),
            annual_interest_rate=Decimal('9'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2026, 1, 1), maturity_date=date(2028, 1, 1),
        )
        result = json.loads(self.tools['get_loan_details'].invoke({'loan_name': 'Secret'}))
        self.assertIn('error', result)

    def test_calculate_loan_scenario(self):
        Loan.objects.create(
            user=self.user, loan_name='Home Loan', loan_type=Loan.LoanType.HOME,
            original_principal=Decimal('100000'), outstanding_principal=Decimal('100000'),
            annual_interest_rate=Decimal('12'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            payment_frequency=Loan.PaymentFrequency.MONTHLY,
            start_date=date(2020, 1, 1), maturity_date=date(2036, 1, 1),
        )
        result = json.loads(self.tools['calculate_loan_scenario'].invoke({'loan_name': 'Home Loan', 'extra_payment': 2000}))
        self.assertIn('baseline', result)
        self.assertEqual(len(result['scenarios']), 1)
        self.assertGreater(Decimal(result['scenarios'][0]['interest_saved']), Decimal('0'))

    def test_calculate_loan_scenario_missing_loan(self):
        result = json.loads(self.tools['calculate_loan_scenario'].invoke({'loan_name': 'nope', 'extra_payment': 100}))
        self.assertIn('error', result)

    def test_get_upcoming_payments(self):
        Loan.objects.create(
            user=self.user, loan_name='Due Soon', loan_type=Loan.LoanType.PERSONAL,
            original_principal=Decimal('1000'), outstanding_principal=Decimal('1000'),
            annual_interest_rate=Decimal('9'), interest_calculation_method=Loan.InterestMethod.EMI_AMORTIZATION,
            start_date=date(2020, 1, 1), maturity_date=date(2028, 1, 1),
            next_due_date=date.today(),
        )
        result = json.loads(self.tools['get_upcoming_payments'].invoke({'days': 30}))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['loan_name'], 'Due Soon')

    def test_get_budget_status(self):
        today = date.today()
        Budget.objects.create(user=self.user, category='Food', amount=Decimal('1000'), month=today.month, year=today.year)
        Transaction.objects.create(
            user=self.user, transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal('600'), category='Food', transaction_date=today,
        )
        result = json.loads(self.tools['get_budget_status'].invoke({}))
        self.assertEqual(result['budgets'][0]['category'], 'Food')
        self.assertEqual(result['budgets'][0]['status'], 'APPROACHING')

    def test_get_budget_status_empty(self):
        result = json.loads(self.tools['get_budget_status'].invoke({'month': 1, 'year': 2020}))
        self.assertEqual(result['budgets'], [])


class ChatViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.chat_url = reverse('ai-chat')

    @patch('apps.ai_assistant.views.get_ai_response')
    def test_send_message_persists_both_sides(self, mock_get_response):
        mock_get_response.return_value = 'You spent nothing this month.'

        response = self.client.post(self.chat_url, {'message': 'How much did I spend?'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['user_message']['content'], 'How much did I spend?')
        self.assertEqual(response.data['assistant_message']['content'], 'You spent nothing this month.')
        self.assertEqual(ChatMessage.objects.filter(user=self.user).count(), 2)

    @patch('apps.ai_assistant.views.get_ai_response')
    def test_history_passed_to_agent_excludes_other_users(self, mock_get_response):
        mock_get_response.return_value = 'ok'
        ChatMessage.objects.create(user=self.other_user, role=ChatMessage.Role.USER, content='secret question')

        self.client.post(self.chat_url, {'message': 'hello'})
        _, kwargs = mock_get_response.call_args
        contents = [h['content'] for h in kwargs['history']]
        self.assertNotIn('secret question', contents)

    def test_empty_message_rejected(self):
        response = self.client.post(self.chat_url, {'message': '   '})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.ai_assistant.views.get_ai_response')
    def test_ai_service_error_returns_502_and_does_not_persist_user_message(self, mock_get_response):
        mock_get_response.side_effect = Exception('network exploded')

        response = self.client.post(self.chat_url, {'message': 'hello'})
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertFalse(response.data['success'])
        self.assertEqual(ChatMessage.objects.count(), 0)

    @patch('apps.ai_assistant.views.get_ai_response')
    def test_missing_api_key_returns_503(self, mock_get_response):
        mock_get_response.side_effect = RuntimeError('AI_API_KEY is not configured.')

        response = self.client.post(self.chat_url, {'message': 'hello'})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch('apps.ai_assistant.views.get_ai_response')
    def test_list_history_only_returns_own_messages(self, mock_get_response):
        mock_get_response.return_value = 'ok'
        self.client.post(self.chat_url, {'message': 'hello'})
        ChatMessage.objects.create(user=self.other_user, role=ChatMessage.Role.USER, content='not mine')

        response = self.client.get(self.chat_url)
        contents = [m['content'] for m in response.data['results']]
        self.assertIn('hello', contents)
        self.assertNotIn('not mine', contents)

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.chat_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
