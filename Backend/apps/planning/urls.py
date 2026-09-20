from django.urls import path

from .views import RepaymentPlanDetailView, RepaymentPlanGenerateView, RepaymentPlanListView

urlpatterns = [
    path('', RepaymentPlanListView.as_view(), name='repayment-plan-list'),
    path('generate/', RepaymentPlanGenerateView.as_view(), name='repayment-plan-generate'),
    path('<int:pk>/', RepaymentPlanDetailView.as_view(), name='repayment-plan-detail'),
]
