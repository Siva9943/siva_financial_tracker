from rest_framework.routers import DefaultRouter

from .views import FinancialGoalViewSet

_router = DefaultRouter()
_router.register('', FinancialGoalViewSet, basename='goal')

goal_urlpatterns = _router.urls
