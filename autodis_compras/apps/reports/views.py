"""
Views para el módulo de reportes.
Genera reportes dinámicos desde los datos de solicitudes y presupuestos.
"""

from decimal import Decimal
from django.db.models import Sum, Count, Q, F
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from autodis_compras.apps.requests.models import PurchaseRequest
from autodis_compras.apps.budgets.models import Budget
from autodis_compras.apps.users.models import Area, CostCenter


class ExpensesByPeriodView(APIView):
    """Reporte de gastos por período (mes/trimestre/año)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        area_id = request.query_params.get('area')
        cost_center_id = request.query_params.get('cost_center')
        category_id = request.query_params.get('category')

        if not year:
            return Response({'error': 'El parámetro year es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        approved_statuses = [
            PurchaseRequest.APROBADA,
            PurchaseRequest.EN_PROCESO,
            PurchaseRequest.COMPRADA,
            PurchaseRequest.COMPLETADA,
        ]

        qs = PurchaseRequest.objects.filter(
            status__in=approved_statuses,
            created_at__year=year,
        )

        if month:
            qs = qs.filter(created_at__month=month)
        if area_id:
            qs = qs.filter(cost_center__area_id=area_id)
        if cost_center_id:
            qs = qs.filter(cost_center_id=cost_center_id)
        if category_id:
            qs = qs.filter(category_id=category_id)

        by_category = qs.values(
            'category__name'
        ).annotate(
            total=Sum('estimated_amount'),
            count=Count('id'),
        ).order_by('-total')

        by_cost_center = qs.values(
            'cost_center__code', 'cost_center__name'
        ).annotate(
            total=Sum('estimated_amount'),
            count=Count('id'),
        ).order_by('-total')

        totals = qs.aggregate(
            total_estimated=Sum('estimated_amount'),
            total_actual=Sum('actual_amount'),
            total_count=Count('id'),
        )

        return Response({
            'filters': {'year': year, 'month': month, 'area': area_id, 'cost_center': cost_center_id, 'category': category_id},
            'totals': totals,
            'by_category': list(by_category),
            'by_cost_center': list(by_cost_center),
        })


class BudgetComparisonView(APIView):
    """Reporte de comparación presupuesto vs gasto real."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not year:
            return Response({'error': 'El parámetro year es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        budgets_qs = Budget.objects.select_related('cost_center', 'category').filter(year=year)
        if month:
            budgets_qs = budgets_qs.filter(month=month)

        results = []
        for budget in budgets_qs:
            spent = budget.get_spent_amount()
            results.append({
                'cost_center': budget.cost_center.code,
                'cost_center_name': budget.cost_center.name,
                'category': budget.category.name,
                'year': budget.year,
                'month': budget.month,
                'budgeted': budget.amount,
                'spent': spent,
                'available': budget.amount - spent,
                'utilization_pct': float(budget.get_utilization_percentage()),
                'exceeded': spent > budget.amount,
            })

        return Response({
            'filters': {'year': year, 'month': month},
            'results': results,
        })


class ExpensesByEmployeeView(APIView):
    """Reporte de gastos por empleado."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not year:
            return Response({'error': 'El parámetro year es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        approved_statuses = [
            PurchaseRequest.APROBADA,
            PurchaseRequest.EN_PROCESO,
            PurchaseRequest.COMPRADA,
            PurchaseRequest.COMPLETADA,
        ]

        qs = PurchaseRequest.objects.filter(
            status__in=approved_statuses,
            created_at__year=year,
        )
        if month:
            qs = qs.filter(created_at__month=month)

        by_employee = qs.values(
            'requester__first_name', 'requester__last_name', 'requester__email',
            'requester__area__name',
        ).annotate(
            total=Sum('estimated_amount'),
            count=Count('id'),
        ).order_by('-total')

        return Response({
            'filters': {'year': year, 'month': month},
            'results': list(by_employee),
        })


class TopSuppliersView(APIView):
    """Reporte de proveedores más utilizados."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        year = request.query_params.get('year')

        completed_statuses = [
            PurchaseRequest.COMPRADA,
            PurchaseRequest.COMPLETADA,
        ]

        qs = PurchaseRequest.objects.filter(
            status__in=completed_statuses,
        ).exclude(actual_supplier='')

        if year:
            qs = qs.filter(created_at__year=year)

        by_supplier = qs.values(
            'actual_supplier'
        ).annotate(
            total=Sum('actual_amount'),
            count=Count('id'),
        ).order_by('-total')[:20]

        return Response({
            'filters': {'year': year},
            'results': list(by_supplier),
        })


class DashboardSummaryView(APIView):
    """Resumen general para el dashboard."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        from django.utils import timezone
        now = timezone.now()

        base_qs = PurchaseRequest.objects.all()
        if not (user.is_finance() or user.is_general_director()):
            if user.is_manager():
                base_qs = base_qs.filter(requester__area=user.area)
            else:
                base_qs = base_qs.filter(requester=user)

        pending_manager = base_qs.filter(status=PurchaseRequest.PENDIENTE_GERENTE).count()
        pending_finance = base_qs.filter(status=PurchaseRequest.APROBADA_POR_GERENTE).count()
        in_process = base_qs.filter(status=PurchaseRequest.EN_PROCESO).count()
        completed_this_month = base_qs.filter(
            status=PurchaseRequest.COMPLETADA,
            created_at__year=now.year,
            created_at__month=now.month,
        ).count()

        monthly_spend = base_qs.filter(
            status__in=[
                PurchaseRequest.APROBADA, PurchaseRequest.EN_PROCESO,
                PurchaseRequest.COMPRADA, PurchaseRequest.COMPLETADA,
            ],
            created_at__year=now.year,
            created_at__month=now.month,
        ).aggregate(total=Sum('estimated_amount'))['total'] or Decimal('0.00')

        return Response({
            'pending_manager_approval': pending_manager,
            'pending_finance_approval': pending_finance,
            'in_process': in_process,
            'completed_this_month': completed_this_month,
            'monthly_spend': monthly_spend,
        })
