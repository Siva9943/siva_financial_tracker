from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from services.goal_service import GoalContributionError, record_contribution

from .filters import FinancialGoalFilter
from .models import FinancialGoal
from .serializers import FinancialGoalSerializer, GoalContributionCreateSerializer, GoalContributionSerializer


class FinancialGoalViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialGoalSerializer
    filterset_class = FinancialGoalFilter
    search_fields = ('name',)
    ordering_fields = ('target_date', 'priority', 'created_at')

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'])
    def contributions(self, request, pk=None):
        goal = self.get_object()

        if request.method == 'GET':
            return Response({'success': True, 'results': GoalContributionSerializer(goal.contributions.all(), many=True).data})

        serializer = GoalContributionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            contribution = record_contribution(goal, **serializer.validated_data)
        except GoalContributionError as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=status.HTTP_400_BAD_REQUEST)

        goal.refresh_from_db()
        return Response(
            {
                'success': True,
                'message': 'Contribution recorded successfully.',
                'contribution': GoalContributionSerializer(contribution).data,
                'goal': FinancialGoalSerializer(goal).data,
            },
            status=status.HTTP_201_CREATED,
        )
