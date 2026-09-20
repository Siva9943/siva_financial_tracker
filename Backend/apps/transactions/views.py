from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from services.transaction_service import generate_due_transactions

from .aggregations import category_breakdown, monthly_trend, monthly_trend_by_type, period_totals
from .filters import RecurringTransactionFilter, TransactionFilter
from .models import RecurringTransaction, Transaction
from .serializers import ExpenseSerializer, IncomeSerializer, RecurringTransactionSerializer, TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter
    search_fields = ('description', 'reference', 'category')
    ordering_fields = ('transaction_date', 'amount', 'created_at')

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        queryset = self.get_queryset()
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        return Response(
            {
                'success': True,
                'totals': period_totals(queryset, today=date.today()),
                'breakdown': category_breakdown(queryset, date_from=date_from, date_to=date_to),
                'monthly_trend': monthly_trend_by_type(queryset, today=date.today()),
            }
        )


class TypeLockedTransactionViewSet(TransactionViewSet):
    """Base for Income/Expense endpoints: same engine, fixed transaction_type."""

    transaction_type = None

    def get_queryset(self):
        return super().get_queryset().filter(transaction_type=self.transaction_type)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, transaction_type=self.transaction_type)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        queryset = self.get_queryset()
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        return Response(
            {
                'success': True,
                'totals': period_totals(queryset, today=date.today()),
                'breakdown': category_breakdown(queryset, date_from=date_from, date_to=date_to),
                'monthly_trend': monthly_trend(queryset, today=date.today()),
            }
        )


class IncomeViewSet(TypeLockedTransactionViewSet):
    serializer_class = IncomeSerializer
    transaction_type = Transaction.TransactionType.INCOME


class ExpenseViewSet(TypeLockedTransactionViewSet):
    serializer_class = ExpenseSerializer
    transaction_type = Transaction.TransactionType.EXPENSE


class RecurringTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringTransactionSerializer
    filterset_class = RecurringTransactionFilter
    ordering_fields = ('next_run_date', 'amount', 'created_at')

    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate_due(self, request):
        results = generate_due_transactions(request.user)
        generated_count = sum(len(dates) for dates in results.values())
        return Response(
            {
                'success': True,
                'message': f'Generated {generated_count} transaction(s).',
                'generated': results,
            }
        )
