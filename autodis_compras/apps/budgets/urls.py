"""
URLs para el módulo de presupuestos.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ItemViewSet, BudgetViewSet, BudgetHistoryViewSet

app_name = 'budgets'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', ItemViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'budget-history', BudgetHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
