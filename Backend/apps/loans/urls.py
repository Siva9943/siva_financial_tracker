from rest_framework.routers import DefaultRouter

from .views import LoanViewSet

_router = DefaultRouter()
_router.register('', LoanViewSet, basename='loan')

loan_urlpatterns = _router.urls
