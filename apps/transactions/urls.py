from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet, CategoryViewSet, TagViewSet,
    TransactionViewSet, BudgetViewSet,
    CurrencyViewSet, ExchangeRateViewSet
)

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'exchange-rates', ExchangeRateViewSet, basename='exchange-rate')

urlpatterns = [
    path('api/', include(router.urls)),
]
