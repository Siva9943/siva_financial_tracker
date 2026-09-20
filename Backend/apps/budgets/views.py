from rest_framework import viewsets
from rest_framework.response import Response

from services.budget_service import build_spent_lookup

from .filters import BudgetFilter
from .models import Budget
from .serializers import BudgetSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    filterset_class = BudgetFilter
    search_fields = ('category',)
    ordering_fields = ('year', 'month', 'category', 'amount')

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        budgets = page if page is not None else queryset

        context = self.get_serializer_context()
        context['spent_lookup'] = build_spent_lookup(request.user, budgets)
        serializer = self.get_serializer(budgets, many=True, context=context)

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
