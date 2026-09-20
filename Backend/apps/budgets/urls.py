from rest_framework.routers import DefaultRouter

from .views import BudgetViewSet

_router = DefaultRouter()
_router.register('', BudgetViewSet, basename='budget')

budget_urlpatterns = _router.urls
