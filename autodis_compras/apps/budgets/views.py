"""
ViewSets para el modulo de presupuestos.
"""

from decimal import Decimal
from django.db.models import Avg
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Category, Item, Budget, BudgetHistory
from .serializers import (
    CategorySerializer, ItemSerializer, BudgetSerializer, BudgetHistorySerializer,
)
from autodis_compras.apps.users.models import CostCenter


class IsFinanceOrDirector(permissions.BasePermission):
    """Solo Finanzas o Direccion General pueden modificar presupuestos."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.can_manage_budgets()


@extend_schema_view(list=extend_schema(tags=['Categorías']), retrieve=extend_schema(tags=['Categorías']),
                     create=extend_schema(tags=['Categorías']), update=extend_schema(tags=['Categorías']),
                     partial_update=extend_schema(tags=['Categorías']), destroy=extend_schema(tags=['Categorías']))
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name']


@extend_schema_view(list=extend_schema(tags=['Items']), retrieve=extend_schema(tags=['Items']),
                     create=extend_schema(tags=['Items']), update=extend_schema(tags=['Items']),
                     partial_update=extend_schema(tags=['Items']), destroy=extend_schema(tags=['Items']))
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.select_related('category').all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'category']


@extend_schema_view(
    list=extend_schema(tags=['Presupuestos']), retrieve=extend_schema(tags=['Presupuestos']),
    create=extend_schema(tags=['Presupuestos']), update=extend_schema(tags=['Presupuestos']),
    partial_update=extend_schema(tags=['Presupuestos']), destroy=extend_schema(tags=['Presupuestos']),
    summary=extend_schema(tags=['Presupuestos']), copy_month=extend_schema(tags=['Presupuestos']),
    project_from_previous_year=extend_schema(tags=['Presupuestos']),
    close_month=extend_schema(tags=['Presupuestos']), reopen_month=extend_schema(tags=['Presupuestos']),
    import_excel=extend_schema(tags=['Presupuestos']),
)
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
        if budget.is_closed:
            raise PermissionDenied('No se puede modificar un mes cerrado.')
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
        """Resumen de presupuestos por anio/mes."""
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        qs = self.get_queryset()
        if year:
            qs = qs.filter(year=year)
        if month:
            qs = qs.filter(month=month)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def copy_month(self, request):
        """Copia presupuestos de un mes origen a un mes destino."""
        source_year = request.data.get('source_year')
        source_month = request.data.get('source_month')
        target_year = request.data.get('target_year')
        target_month = request.data.get('target_month')

        if not all([source_year, source_month, target_year, target_month]):
            return Response(
                {'error': 'Se requieren source_year, source_month, target_year y target_month.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_budgets = Budget.objects.filter(year=source_year, month=source_month)
        if not source_budgets.exists():
            return Response(
                {'error': 'No hay presupuestos en el mes origen.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_count = 0
        skipped_count = 0
        for budget in source_budgets:
            _, created = Budget.objects.get_or_create(
                cost_center=budget.cost_center,
                category=budget.category,
                year=int(target_year),
                month=int(target_month),
                defaults={'amount': budget.amount},
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        return Response({
            'message': f'Copiados {created_count} presupuestos. {skipped_count} ya existian.',
            'created': created_count,
            'skipped': skipped_count,
        })

    @action(detail=False, methods=['post'])
    def project_from_previous_year(self, request):
        """Proyecta presupuestos para un anio basado en el promedio del anio anterior."""
        source_year = request.data.get('source_year')
        target_year = request.data.get('target_year')
        target_month = request.data.get('target_month')

        if not all([source_year, target_year]):
            return Response(
                {'error': 'Se requieren source_year y target_year.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_year = int(source_year)
        target_year = int(target_year)

        averages = Budget.objects.filter(year=source_year).values(
            'cost_center', 'category'
        ).annotate(avg_amount=Avg('amount'))

        if not averages:
            return Response(
                {'error': f'No hay presupuestos en el anio {source_year}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_count = 0
        months = [int(target_month)] if target_month else range(1, 13)

        for avg in averages:
            for month in months:
                _, created = Budget.objects.get_or_create(
                    cost_center_id=avg['cost_center'],
                    category_id=avg['category'],
                    year=target_year,
                    month=month,
                    defaults={'amount': avg['avg_amount'].quantize(Decimal('0.01'))},
                )
                if created:
                    created_count += 1

        return Response({
            'message': f'Proyectados {created_count} presupuestos para {target_year}.',
            'created': created_count,
        })

    @action(detail=False, methods=['post'])
    def close_month(self, request):
        """Cierra un mes para impedir modificaciones."""
        year = request.data.get('year')
        month = request.data.get('month')

        if not all([year, month]):
            return Response(
                {'error': 'Se requieren year y month.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = Budget.objects.filter(
            year=year, month=month, is_closed=False
        ).update(is_closed=True)

        return Response({
            'message': f'Cerrados {updated} presupuestos para {year}/{int(month):02d}.',
            'closed': updated,
        })

    @action(detail=False, methods=['post'])
    def reopen_month(self, request):
        """Reabre un mes cerrado (solo Finanzas)."""
        year = request.data.get('year')
        month = request.data.get('month')

        if not all([year, month]):
            return Response(
                {'error': 'Se requieren year y month.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.is_finance():
            return Response(
                {'error': 'Solo Finanzas puede reabrir meses.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        updated = Budget.objects.filter(
            year=year, month=month, is_closed=True
        ).update(is_closed=False)

        return Response({
            'message': f'Reabiertos {updated} presupuestos para {year}/{int(month):02d}.',
            'reopened': updated,
        })

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def import_excel(self, request):
        """Importa presupuestos desde un archivo Excel.
        Formato: columnas cost_center_code, category_code, year, month, amount
        """
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'Se requiere un archivo Excel.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not file.name.endswith(('.xlsx', '.xls')):
            return Response(
                {'error': 'El archivo debe ser formato Excel (.xlsx o .xls).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import openpyxl
        try:
            wb = openpyxl.load_workbook(file, read_only=True)
            ws = wb.active
        except Exception as e:
            return Response(
                {'error': f'Error al leer el archivo: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rows = list(ws.iter_rows(min_row=2, values_only=True))
        if not rows:
            return Response(
                {'error': 'El archivo no contiene datos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cost_centers = {cc.code: cc for cc in CostCenter.objects.all()}
        categories = {cat.code: cat for cat in Category.objects.all()}

        created_count = 0
        updated_count = 0
        errors = []

        for i, row in enumerate(rows, start=2):
            if len(row) < 5:
                errors.append(f'Fila {i}: datos insuficientes')
                continue

            cc_code, cat_code, year, month, amount = row[:5]

            if cc_code not in cost_centers:
                errors.append(f'Fila {i}: centro de costos "{cc_code}" no encontrado')
                continue
            if cat_code not in categories:
                errors.append(f'Fila {i}: categoria "{cat_code}" no encontrada')
                continue

            try:
                amount = Decimal(str(amount))
            except (ValueError, TypeError):
                errors.append(f'Fila {i}: monto invalido "{amount}"')
                continue

            budget, created = Budget.objects.update_or_create(
                cost_center=cost_centers[cc_code],
                category=categories[cat_code],
                year=int(year),
                month=int(month),
                defaults={'amount': amount},
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        return Response({
            'message': f'Importacion completada: {created_count} creados, {updated_count} actualizados.',
            'created': created_count,
            'updated': updated_count,
            'errors': errors[:20],
        })


@extend_schema_view(list=extend_schema(tags=['Historial Presupuestos']),
                     retrieve=extend_schema(tags=['Historial Presupuestos']))
class BudgetHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BudgetHistory.objects.select_related('budget', 'changed_by').all()
    serializer_class = BudgetHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['budget', 'changed_by']
    ordering_fields = ['created_at']
