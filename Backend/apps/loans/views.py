from datetime import date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from services.loan_payment_service import LoanPaymentError, record_loan_payment
from services.loan_priority_service import STRATEGIES, rank_loans

from .aggregations import loan_summary
from .filters import LoanFilter
from .models import Loan
from .schedule import build_schedule_response, compare_extra_payment_scenarios
from .serializers import (
    LoanCalculatorSerializer,
    LoanPaymentCreateSerializer,
    LoanPaymentSerializer,
    LoanReorderSerializer,
    LoanSerializer,
    LoanSimulatorSerializer,
)


class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    filterset_class = LoanFilter
    search_fields = ('loan_name', 'lender', 'notes')
    ordering_fields = ('next_due_date', 'annual_interest_rate', 'outstanding_principal', 'created_at')

    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        return Response({'success': True, **loan_summary(self.get_queryset())})

    @action(detail=True, methods=['get'])
    def amortization(self, request, pk=None):
        loan = self.get_object()
        result = build_schedule_response(
            principal=loan.original_principal,
            annual_rate=loan.annual_interest_rate,
            method=loan.interest_calculation_method,
            frequency=loan.payment_frequency,
            start_date=loan.start_date,
            maturity_date=loan.maturity_date,
            emi=loan.emi_amount,
        )
        return Response({'success': True, **result})

    @action(detail=True, methods=['get', 'post'])
    def payments(self, request, pk=None):
        loan = self.get_object()

        if request.method == 'GET':
            payments = loan.payments.all()
            return Response(
                {'success': True, 'results': LoanPaymentSerializer(payments, many=True).data}
            )

        serializer = LoanPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = record_loan_payment(loan, **serializer.validated_data)
        except LoanPaymentError as exc:
            return Response(
                {'success': False, 'message': str(exc), 'errors': {}}, status=status.HTTP_400_BAD_REQUEST
            )

        loan.refresh_from_db()
        return Response(
            {
                'success': True,
                'message': 'Payment recorded successfully.',
                'payment': LoanPaymentSerializer(payment).data,
                'loan': LoanSerializer(loan).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'])
    def priority(self, request):
        strategy = request.query_params.get('strategy', 'AVALANCHE').upper()
        if strategy not in STRATEGIES:
            return Response(
                {
                    'success': False,
                    'message': f'Unknown strategy "{strategy}". Choose one of {", ".join(STRATEGIES)}.',
                    'errors': {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        loans = self.get_queryset().filter(status__in=(Loan.Status.ACTIVE, Loan.Status.OVERDUE))
        return Response({'success': True, 'strategy': strategy, 'results': rank_loans(loans, strategy)})

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        serializer = LoanReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan_ids = serializer.validated_data['loan_ids']

        loans_by_id = {loan.id: loan for loan in self.get_queryset().filter(id__in=loan_ids)}
        missing = set(loan_ids) - loans_by_id.keys()
        if missing:
            return Response(
                {'success': False, 'message': f'Unknown loan id(s): {sorted(missing)}.', 'errors': {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for position, loan_id in enumerate(loan_ids, start=1):
            loan = loans_by_id[loan_id]
            loan.priority_order = position
            loan.save(update_fields=['priority_order', 'updated_at'])

        return Response({'success': True, 'message': 'Priority order updated.'})


class LoanCalculatorView(APIView):
    def post(self, request):
        serializer = LoanCalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = build_schedule_response(
            principal=data['original_principal'],
            annual_rate=data['annual_interest_rate'],
            method=data['interest_calculation_method'],
            frequency=data['payment_frequency'],
            start_date=data['start_date'],
            maturity_date=data['maturity_date'],
            emi=data.get('emi_amount'),
        )
        return Response({'success': True, **result})


class LoanSimulatorView(APIView):
    def post(self, request):
        serializer = LoanSimulatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if 'loan_id' in data:
            try:
                loan = Loan.objects.get(id=data['loan_id'], user=request.user)
            except Loan.DoesNotExist:
                return Response(
                    {'success': False, 'message': 'Loan not found.', 'errors': {}}, status=status.HTTP_404_NOT_FOUND
                )
            if loan.maturity_date <= date.today():
                return Response(
                    {'success': False, 'message': 'This loan has already reached its maturity date.', 'errors': {}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            params = dict(
                principal=loan.outstanding_principal,
                annual_rate=loan.annual_interest_rate,
                method=loan.interest_calculation_method,
                frequency=loan.payment_frequency,
                start_date=date.today(),
                maturity_date=loan.maturity_date,
                emi=loan.emi_amount,
            )
        else:
            params = dict(
                principal=data['original_principal'],
                annual_rate=data['annual_interest_rate'],
                method=data['interest_calculation_method'],
                frequency=data['payment_frequency'],
                start_date=data['start_date'],
                maturity_date=data['maturity_date'],
                emi=data.get('emi_amount'),
            )

        try:
            result = compare_extra_payment_scenarios(**params, extra_payments=data['extra_payment_scenarios'])
        except ValueError as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'success': True, **result})
