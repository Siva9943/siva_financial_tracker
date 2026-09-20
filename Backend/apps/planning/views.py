from django.db import transaction as db_transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.loans.models import Loan
from services.repayment_service import RepaymentPlanError, generate_repayment_plan

from .models import PlanItem, RepaymentPlan
from .serializers import RepaymentPlanDetailSerializer, RepaymentPlanGenerateSerializer, RepaymentPlanListSerializer


class RepaymentPlanListView(generics.ListAPIView):
    serializer_class = RepaymentPlanListSerializer

    def get_queryset(self):
        return RepaymentPlan.objects.filter(user=self.request.user)


class RepaymentPlanDetailView(generics.RetrieveAPIView):
    serializer_class = RepaymentPlanDetailSerializer

    def get_queryset(self):
        return RepaymentPlan.objects.filter(user=self.request.user).prefetch_related('items')


class RepaymentPlanGenerateView(APIView):
    def post(self, request):
        serializer = RepaymentPlanGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        loans = Loan.objects.filter(user=request.user, status__in=(Loan.Status.ACTIVE, Loan.Status.OVERDUE))

        try:
            result = generate_repayment_plan(
                loans,
                strategy=data['strategy'],
                monthly_income=data['monthly_income'],
                essential_expenses=data['essential_expenses'],
                emergency_savings_allocation=data['emergency_savings_allocation'],
                extra_payment=data['extra_payment'],
            )
        except RepaymentPlanError as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            plan = RepaymentPlan.objects.create(
                user=request.user,
                strategy=data['strategy'],
                monthly_income=data['monthly_income'],
                essential_expenses=data['essential_expenses'],
                emergency_savings_allocation=data['emergency_savings_allocation'],
                extra_payment=data['extra_payment'],
                total_existing_emi=result['total_existing_emi'],
                months_remaining=result['months_remaining'],
                expected_payoff_date=result['expected_payoff_date'],
                total_interest=result['total_interest'],
                total_payment=result['total_payment'],
                assumptions=result['assumptions'],
            )
            PlanItem.objects.bulk_create(
                PlanItem(
                    plan=plan,
                    month_number=item['month_number'],
                    month_date=item['month_date'],
                    loan_id=item['loan_id'],
                    loan_name=item['loan_name'],
                    normal_emi=item['normal_emi'],
                    extra_payment=item['extra_payment'],
                    principal_paid=item['principal_paid'],
                    interest_paid=item['interest_paid'],
                    closing_balance=item['closing_balance'],
                )
                for item in result['items']
            )

        return Response(
            {
                'success': True,
                'message': 'Repayment plan generated successfully.',
                'excluded_loans': result['excluded_loans'],
                'plan': RepaymentPlanDetailSerializer(plan).data,
            },
            status=status.HTTP_201_CREATED,
        )
