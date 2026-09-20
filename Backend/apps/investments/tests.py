from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.goals.models import FinancialGoal
from apps.notifications.models import Notification
from services.investment_analytics_service import InvestmentAnalyticsError, get_contribution_trend, get_investment_analytics
from services.investment_service import InvestmentTransactionError, record_investment_transaction
from services.portfolio_snapshot_service import create_or_update_snapshot

from .models import Investment, InvestmentTransaction, PortfolioSnapshot
from .tasks import create_daily_portfolio_snapshot, remind_stale_investment_prices

User = get_user_model()


class InvestmentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def _make_investment(self, **overrides):
        defaults = dict(
            user=self.user,
            name='Reliance Industries',
            symbol='RELIANCE',
            investment_type=Investment.InvestmentType.STOCK,
            platform='Zerodha',
        )
        defaults.update(overrides)
        return Investment.objects.create(**defaults)

    def test_create_investment_with_defaults(self):
        investment = self._make_investment()
        self.assertEqual(investment.quantity, 0)
        self.assertEqual(investment.total_invested, 0)
        self.assertEqual(investment.status, Investment.Status.ACTIVE)

    def test_quantity_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._make_investment(quantity=Decimal('-1'))

    def test_current_price_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._make_investment(current_price=Decimal('-10'))

    def test_investment_can_link_to_a_financial_goal(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Retirement',
            goal_type=FinancialGoal.GoalType.CUSTOM,
            target_amount=Decimal('500000'),
            target_date=date(2040, 1, 1),
        )
        investment = self._make_investment(linked_goal=goal)
        self.assertEqual(investment.linked_goal_id, goal.id)
        self.assertEqual(goal.investments.count(), 1)

    def test_deleting_goal_sets_linked_goal_null_not_cascade(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Retirement',
            goal_type=FinancialGoal.GoalType.CUSTOM,
            target_amount=Decimal('500000'),
            target_date=date(2040, 1, 1),
        )
        investment = self._make_investment(linked_goal=goal)
        goal.delete()
        investment.refresh_from_db()
        self.assertIsNone(investment.linked_goal_id)

    def test_deleting_user_cascades_to_investments(self):
        self._make_investment()
        self.user.delete()
        self.assertEqual(Investment.objects.count(), 0)


class InvestmentTransactionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.investment = Investment.objects.create(
            user=self.user, name='Reliance Industries', investment_type=Investment.InvestmentType.STOCK,
        )

    def _make_transaction(self, **overrides):
        defaults = dict(
            user=self.user,
            investment=self.investment,
            transaction_type=InvestmentTransaction.TransactionType.BUY,
            transaction_date=date(2026, 1, 10),
            quantity=Decimal('10'),
            price=Decimal('1400'),
            amount=Decimal('14020'),
            fees=Decimal('20'),
        )
        defaults.update(overrides)
        return InvestmentTransaction.objects.create(**defaults)

    def test_create_buy_transaction(self):
        txn = self._make_transaction()
        self.assertEqual(txn.amount, Decimal('14020'))
        self.assertEqual(self.investment.transactions.count(), 1)

    def test_amount_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._make_transaction(amount=Decimal('-1'))

    def test_zero_amount_allowed_at_db_level_for_corporate_actions(self):
        # The DB only forbids negative amounts; services.investment_service is what enforces
        # amount > 0 for cash-moving types and allows 0 for BONUS/SPLIT.
        txn = self._make_transaction(transaction_type=InvestmentTransaction.TransactionType.BONUS, amount=Decimal('0'), price=Decimal('0'))
        self.assertEqual(txn.amount, Decimal('0'))

    def test_quantity_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._make_transaction(quantity=Decimal('-5'))

    def test_fees_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._make_transaction(fees=Decimal('-1'))

    def test_deleting_investment_cascades_to_transactions(self):
        self._make_transaction()
        self.investment.delete()
        self.assertEqual(InvestmentTransaction.objects.count(), 0)


class PortfolioSnapshotModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def test_create_snapshot(self):
        snapshot = PortfolioSnapshot.objects.create(
            user=self.user,
            snapshot_date=date(2026, 3, 18),
            total_invested=Decimal('480000'),
            portfolio_value=Decimal('542500'),
            profit_loss=Decimal('62500'),
            dividend_income=Decimal('3500'),
        )
        self.assertEqual(snapshot.profit_loss, Decimal('62500'))

    def test_duplicate_snapshot_for_same_user_and_date_rejected(self):
        PortfolioSnapshot.objects.create(user=self.user, snapshot_date=date(2026, 3, 18))
        with self.assertRaises(IntegrityError), transaction.atomic():
            PortfolioSnapshot.objects.create(user=self.user, snapshot_date=date(2026, 3, 18))

    def test_same_date_allowed_for_different_users(self):
        other_user = User.objects.create_user(username='bob', password='pass12345')
        PortfolioSnapshot.objects.create(user=self.user, snapshot_date=date(2026, 3, 18))
        PortfolioSnapshot.objects.create(user=other_user, snapshot_date=date(2026, 3, 18))
        self.assertEqual(PortfolioSnapshot.objects.count(), 2)


class InvestmentServiceTests(TestCase):
    """Tests for services.investment_service.record_investment_transaction."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.investment = Investment.objects.create(
            user=self.user, name='Reliance Industries', investment_type=Investment.InvestmentType.STOCK,
        )

    def _post(self, **kwargs):
        defaults = dict(transaction_date=date(2026, 1, 10), today=date(2026, 3, 18))
        defaults.update(kwargs)
        return record_investment_transaction(self.investment, **defaults)

    def test_buy_computes_amount_and_average_price(self):
        txn = self._post(
            transaction_type=InvestmentTransaction.TransactionType.BUY,
            quantity=Decimal('10'), price=Decimal('1400'), fees=Decimal('20'),
        )
        self.investment.refresh_from_db()
        self.assertEqual(txn.amount, Decimal('14000.00'))
        self.assertEqual(txn.fees, Decimal('20.00'))
        self.assertEqual(self.investment.quantity, Decimal('10'))
        self.assertEqual(self.investment.total_invested, Decimal('14000.00'))
        self.assertEqual(self.investment.average_buy_price, Decimal('1400.0000'))

    def test_second_buy_computes_weighted_average(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1600'))
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.quantity, Decimal('20'))
        self.assertEqual(self.investment.total_invested, Decimal('30000.00'))
        self.assertEqual(self.investment.average_buy_price, Decimal('1500.0000'))

    def test_buy_requires_positive_quantity_and_price(self):
        with self.assertRaises(InvestmentTransactionError):
            self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('0'), price=Decimal('100'))
        with self.assertRaises(InvestmentTransactionError):
            self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('0'))

    def test_sell_computes_realized_profit_and_reduces_holding(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        txn = self._post(transaction_type=InvestmentTransaction.TransactionType.SELL, quantity=Decimal('4'), price=Decimal('1600'))
        self.investment.refresh_from_db()
        self.assertEqual(txn.amount, Decimal('6400.00'))
        self.assertEqual(self.investment.quantity, Decimal('6'))
        self.assertEqual(self.investment.realized_profit_loss, Decimal('800.00'))  # (1600-1400)*4
        self.assertEqual(self.investment.total_invested, Decimal('8400.00'))  # 14000 - 1400*4
        self.assertEqual(self.investment.average_buy_price, Decimal('1400.0000'))  # unchanged by a sell
        self.assertEqual(self.investment.status, Investment.Status.ACTIVE)

    def test_selling_entire_position_closes_investment(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        self._post(transaction_type=InvestmentTransaction.TransactionType.SELL, quantity=Decimal('10'), price=Decimal('1600'))
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.quantity, Decimal('0'))
        self.assertEqual(self.investment.total_invested, Decimal('0.00'))
        self.assertEqual(self.investment.status, Investment.Status.CLOSED)

    def test_cannot_sell_more_than_held(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        with self.assertRaises(InvestmentTransactionError):
            self._post(transaction_type=InvestmentTransaction.TransactionType.SELL, quantity=Decimal('11'), price=Decimal('1600'))

    def test_cannot_sell_with_no_holdings(self):
        with self.assertRaises(InvestmentTransactionError):
            self._post(transaction_type=InvestmentTransaction.TransactionType.SELL, quantity=Decimal('1'), price=Decimal('100'))

    def test_dividend_increases_dividend_income_only(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        self._post(transaction_type=InvestmentTransaction.TransactionType.DIVIDEND, amount=Decimal('250'))
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.dividend_income, Decimal('250.00'))
        self.assertEqual(self.investment.quantity, Decimal('10'))
        self.assertEqual(self.investment.total_invested, Decimal('14000.00'))

    def test_dividend_requires_positive_amount(self):
        with self.assertRaises(InvestmentTransactionError):
            self._post(transaction_type=InvestmentTransaction.TransactionType.DIVIDEND, amount=Decimal('0'))

    def test_bonus_dilutes_average_price_without_new_cash(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        self._post(transaction_type=InvestmentTransaction.TransactionType.BONUS, quantity=Decimal('10'))
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.quantity, Decimal('20'))
        self.assertEqual(self.investment.total_invested, Decimal('14000.00'))
        self.assertEqual(self.investment.average_buy_price, Decimal('700.0000'))

    def test_split_behaves_like_bonus(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1000'))
        self._post(transaction_type=InvestmentTransaction.TransactionType.SPLIT, quantity=Decimal('10'))
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.quantity, Decimal('20'))
        self.assertEqual(self.investment.average_buy_price, Decimal('500.0000'))

    def test_fee_transaction_does_not_change_holdings(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        txn = self._post(transaction_type=InvestmentTransaction.TransactionType.FEE, fees=Decimal('50'))
        self.investment.refresh_from_db()
        self.assertEqual(txn.fees, Decimal('50.00'))
        self.assertEqual(txn.amount, Decimal('0.00'))
        self.assertEqual(self.investment.quantity, Decimal('10'))
        self.assertEqual(self.investment.total_invested, Decimal('14000.00'))

    def test_fee_requires_positive_fees_or_tax(self):
        with self.assertRaises(InvestmentTransactionError):
            self._post(transaction_type=InvestmentTransaction.TransactionType.FEE)

    def test_deposit_pins_quantity_to_one_for_unit_less_instruments(self):
        fd = Investment.objects.create(user=self.user, name='SBI FD', investment_type=Investment.InvestmentType.FIXED_DEPOSIT)
        record_investment_transaction(
            fd, transaction_type=InvestmentTransaction.TransactionType.DEPOSIT,
            transaction_date=date(2026, 1, 1), amount=Decimal('100000'), today=date(2026, 3, 18),
        )
        fd.refresh_from_db()
        self.assertEqual(fd.quantity, Decimal('1'))
        self.assertEqual(fd.total_invested, Decimal('100000.00'))
        self.assertEqual(fd.average_buy_price, Decimal('100000.00'))

    def test_deposit_on_a_share_backed_holding_does_not_corrupt_quantity(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        self._post(transaction_type=InvestmentTransaction.TransactionType.DEPOSIT, amount=Decimal('2000'))
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.quantity, Decimal('10'))  # must stay 10, not be forced to 1
        self.assertEqual(self.investment.total_invested, Decimal('16000.00'))
        self.assertEqual(self.investment.average_buy_price, Decimal('1600.0000'))

    def test_withdrawal_on_a_share_backed_holding_does_not_corrupt_quantity(self):
        self._post(transaction_type=InvestmentTransaction.TransactionType.BUY, quantity=Decimal('10'), price=Decimal('1400'))
        self._post(transaction_type=InvestmentTransaction.TransactionType.WITHDRAWAL, amount=Decimal('4000'))
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.quantity, Decimal('10'))
        self.assertEqual(self.investment.total_invested, Decimal('10000.00'))
        self.assertEqual(self.investment.average_buy_price, Decimal('1000.0000'))

    def test_withdrawal_reduces_invested_and_closes_when_fully_withdrawn(self):
        fd = Investment.objects.create(user=self.user, name='SBI FD', investment_type=Investment.InvestmentType.FIXED_DEPOSIT)
        record_investment_transaction(
            fd, transaction_type=InvestmentTransaction.TransactionType.DEPOSIT,
            transaction_date=date(2026, 1, 1), amount=Decimal('100000'), today=date(2026, 3, 18),
        )
        record_investment_transaction(
            fd, transaction_type=InvestmentTransaction.TransactionType.WITHDRAWAL,
            transaction_date=date(2026, 3, 1), amount=Decimal('100000'), today=date(2026, 3, 18),
        )
        fd.refresh_from_db()
        self.assertEqual(fd.total_invested, Decimal('0.00'))
        self.assertEqual(fd.quantity, Decimal('0'))
        self.assertEqual(fd.status, Investment.Status.CLOSED)

    def test_cannot_withdraw_more_than_invested(self):
        fd = Investment.objects.create(user=self.user, name='SBI FD', investment_type=Investment.InvestmentType.FIXED_DEPOSIT)
        record_investment_transaction(
            fd, transaction_type=InvestmentTransaction.TransactionType.DEPOSIT,
            transaction_date=date(2026, 1, 1), amount=Decimal('50000'), today=date(2026, 3, 18),
        )
        with self.assertRaises(InvestmentTransactionError):
            record_investment_transaction(
                fd, transaction_type=InvestmentTransaction.TransactionType.WITHDRAWAL,
                transaction_date=date(2026, 3, 1), amount=Decimal('60000'), today=date(2026, 3, 18),
            )

    def test_future_transaction_date_rejected(self):
        with self.assertRaises(InvestmentTransactionError):
            self._post(
                transaction_type=InvestmentTransaction.TransactionType.BUY,
                quantity=Decimal('1'), price=Decimal('100'),
                transaction_date=date(2026, 4, 1), today=date(2026, 3, 18),
            )

    def test_negative_fees_rejected(self):
        with self.assertRaises(InvestmentTransactionError):
            self._post(
                transaction_type=InvestmentTransaction.TransactionType.BUY,
                quantity=Decimal('1'), price=Decimal('100'), fees=Decimal('-5'),
            )

    def test_failed_transaction_does_not_persist_partial_state(self):
        with self.assertRaises(InvestmentTransactionError):
            self._post(transaction_type=InvestmentTransaction.TransactionType.SELL, quantity=Decimal('1'), price=Decimal('100'))
        self.assertEqual(self.investment.transactions.count(), 0)
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.quantity, Decimal('0'))


class InvestmentCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.list_url = reverse('investment-list')

    def _payload(self, **overrides):
        payload = {'name': 'Reliance Industries', 'symbol': 'RELIANCE', 'investment_type': Investment.InvestmentType.STOCK, 'platform': 'Zerodha'}
        payload.update(overrides)
        return payload

    def test_create_investment(self):
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Investment.objects.get().user, self.user)
        self.assertEqual(response.data['status'], 'ACTIVE')
        self.assertIn('return_percentage', response.data)

    def test_negative_current_price_rejected(self):
        response = self.client.post(self.list_url, self._payload(current_price='-5'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_returns_own_investments(self):
        Investment.objects.create(user=self.other_user, name='Other Stock', investment_type=Investment.InvestmentType.STOCK)
        self.client.post(self.list_url, self._payload())
        response = self.client.get(self.list_url)
        self.assertEqual(response.data['count'], 1)

    def test_cannot_access_other_users_investment(self):
        other = Investment.objects.create(user=self.other_user, name='Other Stock', investment_type=Investment.InvestmentType.STOCK)
        response = self.client.get(reverse('investment-detail', args=[other.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_delete_other_users_investment(self):
        other = Investment.objects.create(user=self.other_user, name='Other Stock', investment_type=Investment.InvestmentType.STOCK)
        response = self.client.delete(reverse('investment-detail', args=[other.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Investment.objects.filter(id=other.id).exists())

    def test_linked_goal_scoped_to_own_goals(self):
        other_goal = FinancialGoal.objects.create(
            user=self.other_user, name='House', goal_type=FinancialGoal.GoalType.HOUSE,
            target_amount=Decimal('100000'), target_date=date(2030, 1, 1),
        )
        response = self.client.post(self.list_url, self._payload(linked_goal=other_goal.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_status_is_user_writable(self):
        investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK)
        response = self.client.patch(reverse('investment-detail', args=[investment.id]), {'status': 'ON_HOLD'})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        investment.refresh_from_db()
        self.assertEqual(investment.status, Investment.Status.ON_HOLD)

    def test_invalid_status_rejected(self):
        investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK)
        response = self.client.patch(reverse('investment-detail', args=[investment.id]), {'status': 'PAUSED'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_changing_current_price_stamps_updated_at(self):
        investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price=Decimal('100'))
        self.assertIsNone(investment.current_price_updated_at)

        response = self.client.patch(reverse('investment-detail', args=[investment.id]), {'current_price': '150'})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        investment.refresh_from_db()
        self.assertIsNotNone(investment.current_price_updated_at)

    def test_current_price_updated_at_is_not_client_settable(self):
        investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK)
        response = self.client.patch(reverse('investment-detail', args=[investment.id]), {
            'current_price_updated_at': '2020-01-01T00:00:00Z',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        investment.refresh_from_db()
        self.assertIsNone(investment.current_price_updated_at)

    def test_unchanged_current_price_does_not_stamp_updated_at(self):
        investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price=Decimal('100'))
        response = self.client.patch(reverse('investment-detail', args=[investment.id]), {'current_price': '100'})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        investment.refresh_from_db()
        self.assertIsNone(investment.current_price_updated_at)


class InvestmentTransactionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.investment = Investment.objects.create(user=self.user, name='Reliance Industries', investment_type=Investment.InvestmentType.STOCK)
        self.transactions_url = reverse('investment-transactions', args=[self.investment.id])

    def test_post_buy_transaction(self):
        response = self.client.post(self.transactions_url, {
            'transaction_type': 'BUY', 'transaction_date': '2026-01-10', 'quantity': '10', 'price': '1400', 'fees': '20',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['investment']['quantity'], '10.000000')
        self.assertEqual(response.data['transaction']['amount'], '14000.00')

    def test_invalid_sell_returns_400_not_500(self):
        response = self.client.post(self.transactions_url, {
            'transaction_type': 'SELL', 'transaction_date': '2026-01-10', 'quantity': '10', 'price': '1400',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_post_transaction_to_other_users_investment(self):
        other_investment = Investment.objects.create(user=self.other_user, name='Other', investment_type=Investment.InvestmentType.STOCK)
        url = reverse('investment-transactions', args=[other_investment.id])
        response = self.client.post(url, {'transaction_type': 'BUY', 'transaction_date': '2026-01-10', 'quantity': '1', 'price': '100'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(InvestmentTransaction.objects.filter(investment=other_investment).count(), 0)

    def test_list_transactions(self):
        self.client.post(self.transactions_url, {'transaction_type': 'BUY', 'transaction_date': '2026-01-10', 'quantity': '10', 'price': '1400'})
        response = self.client.get(self.transactions_url)
        self.assertEqual(len(response.data['results']), 1)


class PortfolioEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)

    def _buy(self, investment, quantity, price):
        record_investment_transaction(
            investment, transaction_type=InvestmentTransaction.TransactionType.BUY,
            transaction_date=date(2026, 1, 10), quantity=Decimal(quantity), price=Decimal(price), today=date(2026, 3, 18),
        )

    def test_portfolio_aggregates_across_own_investments_only(self):
        stock = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price=Decimal('1520'))
        self._buy(stock, '10', '1400')

        other_stock = Investment.objects.create(user=self.other_user, name='Infosys', investment_type=Investment.InvestmentType.STOCK, current_price=Decimal('2000'))
        self._buy(other_stock, '10', '1800')

        response = self.client.get(reverse('investment-portfolio'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_invested'], Decimal('14000.00'))
        self.assertEqual(response.data['current_value'], Decimal('15200.00'))
        self.assertEqual(response.data['unrealized_profit_loss'], Decimal('1200.00'))
        self.assertEqual(response.data['investment_count'], 1)

    def test_allocation_by_type_percentages_sum_to_100(self):
        stock = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price=Decimal('1520'))
        self._buy(stock, '10', '1400')
        gold = Investment.objects.create(user=self.user, name='Gold ETF', investment_type=Investment.InvestmentType.GOLD, current_price=Decimal('6000'))
        self._buy(gold, '1', '5000')

        response = self.client.get(reverse('investment-allocation'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        total_pct = sum(row['percentage'] for row in response.data['results'])
        self.assertAlmostEqual(total_pct, 100, delta=0.1)


class InvestmentAnalyticsServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.today = date(2026, 3, 18)
        self.investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price=Decimal('1520'))

    def _buy(self, txn_date, quantity, price):
        record_investment_transaction(
            self.investment, transaction_type=InvestmentTransaction.TransactionType.BUY,
            transaction_date=txn_date, quantity=Decimal(quantity), price=Decimal(price), today=self.today,
        )

    def _dividend(self, txn_date, amount):
        record_investment_transaction(
            self.investment, transaction_type=InvestmentTransaction.TransactionType.DIVIDEND,
            transaction_date=txn_date, amount=Decimal(amount), today=self.today,
        )

    def test_unknown_period_rejected(self):
        with self.assertRaises(InvestmentAnalyticsError):
            get_investment_analytics(self.user, 'decade', today=self.today)

    def test_month_period_scopes_contribution_and_dividend_to_current_month(self):
        self._buy(date(2026, 2, 15), '5', '1000')  # last month — excluded
        self._buy(date(2026, 3, 1), '10', '1400')  # this month — included
        self._dividend(date(2026, 3, 10), '250')

        result = get_investment_analytics(self.user, 'month', today=self.today)
        self.assertEqual(result['contribution'], Decimal('14000.00'))
        self.assertEqual(result['dividend_income'], Decimal('250.00'))
        self.assertEqual(result['total_invested'], Decimal('19000.00'))  # live total across both buys

    def test_year_period_includes_whole_year(self):
        self._buy(date(2026, 1, 5), '5', '1000')
        self._buy(date(2026, 3, 1), '10', '1400')
        result = get_investment_analytics(self.user, 'year', today=self.today)
        self.assertEqual(result['contribution'], Decimal('19000.00'))

    def test_day_period_only_includes_today(self):
        self._buy(date(2026, 3, 17), '5', '1000')
        self._buy(self.today, '2', '1500')
        result = get_investment_analytics(self.user, 'day', today=self.today)
        self.assertEqual(result['contribution'], Decimal('3000.00'))

    def test_contribution_trend_is_zero_filled_and_ordered_for_months(self):
        self._buy(date(2026, 1, 10), '5', '1000')
        self._buy(self.today, '2', '1500')
        trend = get_contribution_trend(self.user, 'month', today=self.today)
        self.assertEqual(len(trend), 12)
        self.assertEqual(trend[-1]['period'], '2026-03')
        by_period = {row['period']: row['contribution'] for row in trend}
        self.assertEqual(by_period['2026-03'], Decimal('3000.00'))
        self.assertEqual(by_period['2026-01'], Decimal('5000.00'))
        self.assertEqual(by_period['2025-12'], Decimal('0.00'))

    def test_contribution_trend_week_buckets_align_to_monday(self):
        self._buy(date(2026, 3, 16), '1', '1000')  # Monday of this week
        trend = get_contribution_trend(self.user, 'week', today=self.today)
        self.assertEqual(trend[-1]['period'], '2026-03-16')
        self.assertEqual(trend[-1]['contribution'], Decimal('1000.00'))


class InvestmentAnalyticsEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.client.force_authenticate(self.user)
        self.investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK)

    def test_analytics_endpoint_defaults_to_month(self):
        response = self.client.get(reverse('investment-analytics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'month')

    def test_analytics_endpoint_rejects_unknown_period(self):
        response = self.client.get(reverse('investment-analytics'), {'period': 'decade'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_contributions_endpoint_returns_series(self):
        response = self.client.get(reverse('investment-contributions'), {'period': 'year'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)


class PortfolioSnapshotServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price=Decimal('1520'))
        record_investment_transaction(
            self.investment, transaction_type=InvestmentTransaction.TransactionType.BUY,
            transaction_date=date(2026, 1, 10), quantity=Decimal('10'), price=Decimal('1400'), today=date(2026, 3, 18),
        )

    def test_create_snapshot_captures_current_portfolio_state(self):
        snapshot = create_or_update_snapshot(self.user, snapshot_date=date(2026, 3, 18))
        self.assertEqual(snapshot.total_invested, Decimal('14000.00'))
        self.assertEqual(snapshot.portfolio_value, Decimal('15200.00'))
        self.assertEqual(snapshot.profit_loss, Decimal('1200.00'))

    def test_running_twice_updates_in_place_not_duplicates(self):
        create_or_update_snapshot(self.user, snapshot_date=date(2026, 3, 18))
        self.investment.current_price = Decimal('1600')
        self.investment.save(update_fields=['current_price'])

        create_or_update_snapshot(self.user, snapshot_date=date(2026, 3, 18))
        self.assertEqual(PortfolioSnapshot.objects.filter(user=self.user).count(), 1)
        snapshot = PortfolioSnapshot.objects.get(user=self.user)
        self.assertEqual(snapshot.portfolio_value, Decimal('16000.00'))

    def test_daily_task_snapshots_only_users_with_investments(self):
        User.objects.create_user(username='bob', password='pass12345')  # no investments
        count = create_daily_portfolio_snapshot(snapshot_date=date(2026, 3, 18))
        self.assertEqual(count, 1)
        self.assertEqual(PortfolioSnapshot.objects.count(), 1)

    def test_daily_task_run_twice_stays_idempotent(self):
        create_daily_portfolio_snapshot(snapshot_date=date(2026, 3, 18))
        create_daily_portfolio_snapshot(snapshot_date=date(2026, 3, 18))
        self.assertEqual(PortfolioSnapshot.objects.count(), 1)


class PortfolioSnapshotEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)

    def test_creating_first_investment_creates_a_snapshot_immediately(self):
        response = self.client.post(reverse('investment-list'), {
            'name': 'Reliance', 'investment_type': Investment.InvestmentType.STOCK,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PortfolioSnapshot.objects.filter(user=self.user).count(), 1)

    def test_recording_a_transaction_updates_todays_snapshot(self):
        investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price=Decimal('1520'))
        self.client.post(reverse('investment-transactions', args=[investment.id]), {
            'transaction_type': 'BUY', 'transaction_date': date.today().isoformat(), 'quantity': '10', 'price': '1400',
        })
        snapshot = PortfolioSnapshot.objects.get(user=self.user, snapshot_date=date.today())
        self.assertEqual(snapshot.total_invested, Decimal('14000.00'))

    def test_snapshots_endpoint_only_returns_own_snapshots(self):
        create_or_update_snapshot(self.user, snapshot_date=date(2026, 1, 1))
        create_or_update_snapshot(self.other_user, snapshot_date=date(2026, 1, 1))
        response = self.client.get(reverse('investment-snapshots'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_snapshots_endpoint_rejects_unknown_range(self):
        response = self.client.get(reverse('investment-snapshots'), {'range': '10Y'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DividendEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(self.user)
        self.investment = Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK)

    def test_dividends_endpoint_lists_own_dividends_only(self):
        record_investment_transaction(
            self.investment, transaction_type=InvestmentTransaction.TransactionType.DIVIDEND,
            transaction_date=date(2026, 2, 1), amount=Decimal('250'), today=date(2026, 3, 18),
        )
        other_investment = Investment.objects.create(user=self.other_user, name='Other', investment_type=Investment.InvestmentType.STOCK)
        record_investment_transaction(
            other_investment, transaction_type=InvestmentTransaction.TransactionType.DIVIDEND,
            transaction_date=date(2026, 2, 1), amount=Decimal('999'), today=date(2026, 3, 18),
        )

        response = self.client.get(reverse('investment-dividends'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['investment_name'], 'Reliance')
        self.assertEqual(response.data['results'][0]['amount'], '250.00')

    def test_dividends_endpoint_excludes_other_transaction_types(self):
        record_investment_transaction(
            self.investment, transaction_type=InvestmentTransaction.TransactionType.BUY,
            transaction_date=date(2026, 1, 10), quantity=Decimal('10'), price=Decimal('1400'), today=date(2026, 3, 18),
        )
        response = self.client.get(reverse('investment-dividends'))
        self.assertEqual(len(response.data['results']), 0)


class StaleInvestmentPriceReminderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.today = date(2026, 3, 18)

    def test_never_updated_price_is_flagged(self):
        Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price_updated_at=None)
        sent = remind_stale_investment_prices(today=self.today)
        self.assertEqual(sent, 1)
        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.notification_type, Notification.NotificationType.STALE_INVESTMENT_PRICE)

    def test_price_updated_31_days_ago_is_flagged(self):
        stale_at = timezone.make_aware(datetime.combine(self.today - timedelta(days=31), datetime.min.time()))
        Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price_updated_at=stale_at)
        sent = remind_stale_investment_prices(today=self.today)
        self.assertEqual(sent, 1)

    def test_recently_updated_price_is_not_flagged(self):
        recent = timezone.make_aware(datetime.combine(self.today - timedelta(days=5), datetime.min.time()))
        Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price_updated_at=recent)
        sent = remind_stale_investment_prices(today=self.today)
        self.assertEqual(sent, 0)

    def test_closed_investment_is_not_flagged(self):
        Investment.objects.create(
            user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK,
            status=Investment.Status.CLOSED, current_price_updated_at=None,
        )
        sent = remind_stale_investment_prices(today=self.today)
        self.assertEqual(sent, 0)

    def test_running_twice_in_the_same_month_does_not_duplicate(self):
        Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price_updated_at=None)
        remind_stale_investment_prices(today=self.today)
        remind_stale_investment_prices(today=self.today)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)

    def test_new_month_allows_a_fresh_reminder(self):
        Investment.objects.create(user=self.user, name='Reliance', investment_type=Investment.InvestmentType.STOCK, current_price_updated_at=None)
        remind_stale_investment_prices(today=self.today)
        remind_stale_investment_prices(today=date(2026, 4, 18))
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 2)
