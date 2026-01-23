"""
Modelos para la gestión de presupuestos, categorías e items.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from autodis_compras.apps.users.models import CostCenter


class Category(models.Model):
    """
    Categorías de presupuesto.
    12 categorías: PAPELERÍA, LIMPIEZA, MANTENIMIENTO MOTOS, etc.
    """
    PAPELERIA = 'PAPELERIA'
    LIMPIEZA = 'LIMPIEZA'
    MANTENIMIENTO_MOTOS = 'MANTENIMIENTO_MOTOS'
    MANTENIMIENTO_AUTOMOVILES = 'MANTENIMIENTO_AUTOMOVILES'
    MANTENIMIENTO_BODEGAS = 'MANTENIMIENTO_BODEGAS'
    VIATICOS = 'VIATICOS'
    SEGURIDAD_HIGIENE = 'SEGURIDAD_HIGIENE'
    PUBLICIDAD_EVENTOS = 'PUBLICIDAD_EVENTOS'
    CONSUMIBLES = 'CONSUMIBLES'
    COMBUSTIBLES = 'COMBUSTIBLES'
    NOMINA = 'NOMINA'
    IMPUESTOS = 'IMPUESTOS'

    CATEGORY_CHOICES = [
        (PAPELERIA, 'Papelería'),
        (LIMPIEZA, 'Limpieza'),
        (MANTENIMIENTO_MOTOS, 'Mantenimiento Motos'),
        (MANTENIMIENTO_AUTOMOVILES, 'Mantenimiento Automóviles'),
        (MANTENIMIENTO_BODEGAS, 'Mantenimiento Bodegas'),
        (VIATICOS, 'Viáticos'),
        (SEGURIDAD_HIGIENE, 'Seguridad e Higiene'),
        (PUBLICIDAD_EVENTOS, 'Publicidad y Eventos'),
        (CONSUMIBLES, 'Consumibles'),
        (COMBUSTIBLES, 'Combustibles'),
        (NOMINA, 'Nómina'),
        (IMPUESTOS, 'Impuestos'),
    ]

    code = models.CharField('Código', max_length=50, choices=CATEGORY_CHOICES, unique=True)
    name = models.CharField('Nombre', max_length=200)
    description = models.TextField('Descripción', blank=True)
    is_active = models.BooleanField('Activa', default=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    """
    Items dentro de cada categoría.
    228 items en total distribuidos en las 12 categorías.
    """
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items', verbose_name='Categoría')
    code = models.CharField('Código', max_length=50, unique=True)
    name = models.CharField('Nombre', max_length=200)
    description = models.TextField('Descripción', blank=True)
    unit = models.CharField('Unidad', max_length=50, blank=True, help_text='Ej: Pieza, Litro, Caja, etc.')
    is_active = models.BooleanField('Activo', default=True, help_text='Los items inactivos no aparecen en nuevas solicitudes')
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Budget(models.Model):
    """
    Presupuestos mensuales por centro de costos y categoría.
    Control de 3 niveles: Centro de Costos, Categoría, Mes.
    """
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, related_name='budgets', verbose_name='Centro de Costos')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='budgets', verbose_name='Categoría')
    year = models.IntegerField('Año')
    month = models.IntegerField('Mes', validators=[MinValueValidator(1)])
    amount = models.DecimalField('Monto Presupuestado', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_closed = models.BooleanField('Cerrado', default=False, help_text='Los meses cerrados no permiten modificaciones')
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        ordering = ['-year', '-month', 'cost_center', 'category']
        unique_together = [['cost_center', 'category', 'year', 'month']]
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['cost_center', 'category', 'year', 'month']),
        ]

    def __str__(self):
        return f"{self.cost_center.code} - {self.category.name} ({self.year}/{self.month:02d}): ${self.amount:,.2f}"

    def get_spent_amount(self):
        """Calcula el monto gastado en solicitudes aprobadas del mes."""
        from autodis_compras.apps.requests.models import PurchaseRequest

        spent = PurchaseRequest.objects.filter(
            cost_center=self.cost_center,
            category=self.category,
            created_at__year=self.year,
            created_at__month=self.month,
            status__in=[
                PurchaseRequest.APROBADA_POR_GERENTE,
                PurchaseRequest.APROBADA,
                PurchaseRequest.EN_PROCESO,
                PurchaseRequest.COMPRADA,
                PurchaseRequest.COMPLETADA,
            ]
        ).aggregate(total=models.Sum('estimated_amount'))['total'] or Decimal('0.00')

        return spent

    def get_available_amount(self):
        """Calcula el monto disponible."""
        return self.amount - self.get_spent_amount()

    def get_utilization_percentage(self):
        """Calcula el porcentaje de utilización del presupuesto."""
        if self.amount == 0:
            return 0
        return (self.get_spent_amount() / self.amount) * 100

    def is_exceeded(self):
        """Verifica si el presupuesto ha sido excedido."""
        return self.get_spent_amount() > self.amount


class BudgetHistory(models.Model):
    """
    Historial de cambios en presupuestos para auditoría.
    """
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='history', verbose_name='Presupuesto')
    previous_amount = models.DecimalField('Monto Anterior', max_digits=12, decimal_places=2)
    new_amount = models.DecimalField('Nuevo Monto', max_digits=12, decimal_places=2)
    changed_by = models.ForeignKey('users.User', on_delete=models.PROTECT, verbose_name='Modificado por')
    reason = models.TextField('Razón del cambio', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de Presupuesto'
        verbose_name_plural = 'Historial de Presupuestos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.budget} - Cambio: ${self.previous_amount} -> ${self.new_amount}"
