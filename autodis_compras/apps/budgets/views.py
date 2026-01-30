"""
ViewSets para el módulo de presupuestos.
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Category, Item, Budget, BudgetHistory
from .serializers import (
    CategorySerializer, ItemSerializer, BudgetSerializer, BudgetHistorySerializer,
)


class IsFinanceOrDirector(permissions.BasePermission):
    """Solo Finanzas o Dirección General pueden modificar presupuestos."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.can_manage_budgets()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name']


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.select_related('category').all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'category']


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.select_related('cost_center', 'category').all()
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['cost_center', 'category', 'year', 'month', 'is_closed']
    ordering_fields = ['year', 'month', 'amount']

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        budget = self.get_object()
        old_amount = budget.amount
        instance = serializer.save()
        new_amount = instance.amount
        if old_amount != new_amount:
            BudgetHistory.objects.create(
                budget=instance,
                previous_amount=old_amount,
                new_amount=new_amount,
                changed_by=self.request.user,
                reason=self.request.data.get('reason', ''),
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Resumen de presupuestos por año/mes."""
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        qs = self.get_queryset()
        if year:
            qs = qs.filter(year=year)
        if month:
            qs = qs.filter(month=month)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class BudgetHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BudgetHistory.objects.select_related('budget', 'changed_by').all()
    serializer_class = BudgetHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['budget', 'changed_by']
    ordering_fields = ['created_at']
