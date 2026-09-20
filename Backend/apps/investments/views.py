from datetime import date

from dateutil.relativedelta import relativedelta
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from services.investment_analytics_service import InvestmentAnalyticsError, get_contribution_trend, get_investment_analytics
from services.investment_performance_service import get_investment_performance, get_portfolio_performance
from services.investment_service import InvestmentTransactionError, record_investment_transaction
from services.portfolio_service import allocation_by_platform, allocation_by_type, build_holdings
from services.portfolio_snapshot_service import create_or_update_snapshot

from .filters import InvestmentFilter, InvestmentTransactionFilter
from .models import Investment, InvestmentTransaction, PortfolioSnapshot
from .serializers import (
    DividendSerializer,
    InvestmentSerializer,
    InvestmentTransactionCreateSerializer,
    InvestmentTransactionSerializer,
    PortfolioSnapshotSerializer,
)

_RANGE_LOOKBACK = {
    '1D': relativedelta(days=1),
    '1W': relativedelta(weeks=1),
    '1M': relativedelta(months=1),
    '3M': relativedelta(months=3),
    '6M': relativedelta(months=6),
    '1Y': relativedelta(years=1),
    '3Y': relativedelta(years=3),
    '5Y': relativedelta(years=5),
}


class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer
    filterset_class = InvestmentFilter
    search_fields = ('name', 'symbol', 'platform')
    ordering_fields = ('name', 'total_invested', 'current_price', 'created_at')

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # So a brand-new account has at least one PortfolioSnapshot point immediately,
        # rather than waiting for the next daily Celery run (skill §11-12 mitigation).
        # Best-effort: the investment is already saved, so a snapshot failure here must
        # never turn an otherwise-successful create into a 500.
        try:
            create_or_update_snapshot(self.request.user)
        except Exception:
            pass

    @action(detail=True, methods=['get', 'post'])
    def transactions(self, request, pk=None):
        investment = self.get_object()

        if request.method == 'GET':
            filtered = InvestmentTransactionFilter(request.query_params, queryset=investment.transactions.all()).qs
            return Response({'success': True, 'results': InvestmentTransactionSerializer(filtered, many=True).data})

        serializer = InvestmentTransactionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            txn = record_investment_transaction(investment, **serializer.validated_data)
        except InvestmentTransactionError as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=status.HTTP_400_BAD_REQUEST)

        investment.refresh_from_db()
        # Best-effort: the transaction is already committed, so a snapshot failure here
        # must never turn an otherwise-successful transaction into a 500.
        try:
            create_or_update_snapshot(request.user)
        except Exception:
            pass
        return Response(
            {
                'success': True,
                'message': 'Transaction recorded successfully.',
                'transaction': InvestmentTransactionSerializer(txn).data,
                'investment': InvestmentSerializer(investment, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        investment = self.get_object()
        return Response({'success': True, **get_investment_performance(investment)})

    @action(detail=False, methods=['get'])
    def portfolio(self, request):
        return Response({'success': True, **get_portfolio_performance(request.user)})

    @action(detail=False, methods=['get'])
    def allocation(self, request):
        holdings = build_holdings(self.get_queryset())
        group_by = request.query_params.get('group_by', 'type')
        rows = allocation_by_platform(holdings) if group_by == 'platform' else allocation_by_type(holdings)
        return Response({'success': True, 'group_by': group_by, 'results': rows})

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        period = request.query_params.get('period', 'month')
        try:
            result = get_investment_analytics(request.user, period)
        except InvestmentAnalyticsError as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True, **result})

    @action(detail=False, methods=['get'])
    def contributions(self, request):
        period = request.query_params.get('period', 'month')
        try:
            series = get_contribution_trend(request.user, period)
        except InvestmentAnalyticsError as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True, 'period': period, 'results': series})

    @action(detail=False, methods=['get'])
    def dividends(self, request):
        dividends = (
            InvestmentTransaction.objects.filter(user=request.user, transaction_type=InvestmentTransaction.TransactionType.DIVIDEND)
            .select_related('investment')
            .order_by('-transaction_date')
        )
        return Response({'success': True, 'results': DividendSerializer(dividends, many=True).data})

    @action(detail=False, methods=['get'])
    def snapshots(self, request):
        range_key = request.query_params.get('range', 'ALL').upper()
        queryset = PortfolioSnapshot.objects.filter(user=request.user).order_by('snapshot_date')

        if range_key != 'ALL':
            if range_key not in _RANGE_LOOKBACK:
                return Response(
                    {'success': False, 'message': f'Unknown range "{range_key}". Choose one of {", ".join(_RANGE_LOOKBACK)}, or ALL.', 'errors': {}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cutoff = date.today() - _RANGE_LOOKBACK[range_key]
            queryset = queryset.filter(snapshot_date__gte=cutoff)

        return Response({'success': True, 'range': range_key, 'results': PortfolioSnapshotSerializer(queryset, many=True).data})
