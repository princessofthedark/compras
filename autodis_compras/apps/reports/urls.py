"""
URLs para el módulo de reportes.
"""

from django.urls import path
from .views import (
    ExpensesByPeriodView,
    BudgetComparisonView,
    ExpensesByEmployeeView,
    TopSuppliersView,
    DashboardSummaryView,
)

app_name = 'reports'

urlpatterns = [
    path('expenses-by-period/', ExpensesByPeriodView.as_view(), name='expenses-by-period'),
    path('budget-comparison/', BudgetComparisonView.as_view(), name='budget-comparison'),
    path('expenses-by-employee/', ExpensesByEmployeeView.as_view(), name='expenses-by-employee'),
    path('top-suppliers/', TopSuppliersView.as_view(), name='top-suppliers'),
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard'),
]
