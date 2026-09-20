from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.ai_assistant.urls import chat_urlpatterns
from apps.analytics.urls import analytics_urlpatterns, dashboard_urlpatterns
from apps.budgets.urls import budget_urlpatterns
from apps.goals.urls import goal_urlpatterns
from apps.investments.urls import investment_urlpatterns
from apps.loans.urls import loan_urlpatterns
from apps.loans.views import LoanCalculatorView, LoanSimulatorView
from apps.notifications.urls import notification_urlpatterns, reminder_urlpatterns
from apps.reports.urls import report_urlpatterns
from apps.transactions.urls import expense_urlpatterns, income_urlpatterns, recurring_urlpatterns, transaction_urlpatterns


def health_check(request):
    return JsonResponse({'success': True, 'message': 'FinTrack API is running', 'errors': {}})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/transactions/', include(transaction_urlpatterns)),
    path('api/income/', include(income_urlpatterns)),
    path('api/expenses/', include(expense_urlpatterns)),
    path('api/recurring-transactions/', include(recurring_urlpatterns)),
    path('api/loans/', include(loan_urlpatterns)),
    path('api/loan-calculator/', LoanCalculatorView.as_view(), name='loan-calculator'),
    path('api/loan-simulator/', LoanSimulatorView.as_view(), name='loan-simulator'),
    path('api/repayment-plan/', include('apps.planning.urls')),
    path('api/budgets/', include(budget_urlpatterns)),
    path('api/dashboard/', include(dashboard_urlpatterns)),
    path('api/analytics/', include(analytics_urlpatterns)),
    path('api/reminders/', include(reminder_urlpatterns)),
    path('api/notifications/', include(notification_urlpatterns)),
    path('api/goals/', include(goal_urlpatterns)),
    path('api/investments/', include(investment_urlpatterns)),
    path('api/ai/', include(chat_urlpatterns)),
    path('api/reports/', include(report_urlpatterns)),
    # Further domain app routers are included here as they are built.
]
