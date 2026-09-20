from rest_framework.routers import DefaultRouter

from .views import InvestmentViewSet

_router = DefaultRouter()
_router.register('', InvestmentViewSet, basename='investment')

investment_urlpatterns = _router.urls
