from rest_framework.routers import DefaultRouter

from .views import ExpenseViewSet, IncomeViewSet, RecurringTransactionViewSet, TransactionViewSet

_transaction_router = DefaultRouter()
_transaction_router.register('', TransactionViewSet, basename='transaction')
transaction_urlpatterns = _transaction_router.urls

_income_router = DefaultRouter()
_income_router.register('', IncomeViewSet, basename='income')
income_urlpatterns = _income_router.urls

_expense_router = DefaultRouter()
_expense_router.register('', ExpenseViewSet, basename='expense')
expense_urlpatterns = _expense_router.urls

_recurring_router = DefaultRouter()
_recurring_router.register('', RecurringTransactionViewSet, basename='recurring-transaction')
recurring_urlpatterns = _recurring_router.urls
