"""
Modelos para la gestión de solicitudes de compra.
"""

from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from autodis_compras.apps.users.models import User, CostCenter
from autodis_compras.apps.budgets.models import Category, Item
import os


def request_attachment_path(instance, filename):
    """Genera la ruta para archivos adjuntos de solicitudes."""
    return f'requests/{instance.request.id}/attachments/{filename}'


class PurchaseRequest(models.Model):
    """
    Solicitud de compra con flujo de aprobación en cascada.
    10 estados: Borrador, Pendiente gerente, Aprobada gerente, Aprobada,
    En proceso, Comprada, Completada, Rechazada gerente, Rechazada Finanzas, Cancelada.
    """
    # Estados de solicitud
    BORRADOR = 'BORRADOR'
    PENDIENTE_GERENTE = 'PENDIENTE_GERENTE'
    APROBADA_POR_GERENTE = 'APROBADA_POR_GERENTE'
    APROBADA = 'APROBADA'
    EN_PROCESO = 'EN_PROCESO'
    COMPRADA = 'COMPRADA'
    COMPLETADA = 'COMPLETADA'
    RECHAZADA_GERENTE = 'RECHAZADA_GERENTE'
    RECHAZADA_FINANZAS = 'RECHAZADA_FINANZAS'
    CANCELADA = 'CANCELADA'

    STATUS_CHOICES = [
        (BORRADOR, 'Borrador'),
        (PENDIENTE_GERENTE, 'Pendiente aprobación gerente'),
        (APROBADA_POR_GERENTE, 'Aprobada por gerente'),
        (APROBADA, 'Aprobada'),
        (EN_PROCESO, 'En proceso de compra'),
        (COMPRADA, 'Comprada'),
        (COMPLETADA, 'Completada'),
        (RECHAZADA_GERENTE, 'Rechazada por gerente'),
        (RECHAZADA_FINANZAS, 'Rechazada por Finanzas/Dir. General'),
        (CANCELADA, 'Cancelada'),
    ]

    # Niveles de urgencia
    NORMAL = 'NORMAL'
    URGENTE = 'URGENTE'

    URGENCY_CHOICES = [
        (NORMAL, 'Normal'),
        (URGENTE, 'Urgente'),
    ]

    # Campos principales
    request_number = models.CharField('Número de Solicitud', max_length=20, unique=True, editable=False)
    requester = models.ForeignKey(User, on_delete=models.PROTECT, related_name='purchase_requests', verbose_name='Solicitante')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, related_name='purchase_requests', verbose_name='Centro de Costos')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='purchase_requests', verbose_name='Categoría')

    # Items (puede ser uno o varios)
    items = models.ManyToManyField(Item, related_name='purchase_requests', verbose_name='Items')

    # Detalles de la solicitud
    description = models.TextField('Descripción detallada')
    suggested_supplier = models.CharField('Proveedor sugerido', max_length=200, blank=True)
    estimated_amount = models.DecimalField('Monto estimado (MXN)', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    required_date = models.DateField('Fecha requerida')
    justification = models.TextField('Justificación')
    budget_excess_justification = models.TextField('Justificación de exceso presupuestal', blank=True)
    urgency = models.CharField('Urgencia', max_length=20, choices=URGENCY_CHOICES, default=NORMAL)

    # Control de estado
    status = models.CharField('Estado', max_length=30, choices=STATUS_CHOICES, default=BORRADOR)

    # Aprobaciones
    manager_approved_at = models.DateTimeField('Aprobado por gerente', null=True, blank=True)
    manager_approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='managed_approvals', verbose_name='Gerente que aprobó', null=True, blank=True)

    final_approved_at = models.DateTimeField('Aprobación final', null=True, blank=True)
    final_approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='final_approvals', verbose_name='Aprobador final', null=True, blank=True)

    # Rechazo
    rejection_reason = models.TextField('Razón de rechazo', blank=True)
    rejected_at = models.DateTimeField('Rechazado', null=True, blank=True)
    rejected_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rejections', verbose_name='Rechazado por', null=True, blank=True)

    # Seguimiento de compra
    purchase_date = models.DateField('Fecha de compra', null=True, blank=True)
    actual_supplier = models.CharField('Proveedor real', max_length=200, blank=True)
    actual_amount = models.DecimalField('Monto real', max_digits=12, decimal_places=2, null=True, blank=True)
    invoice_number = models.CharField('Número de factura', max_length=100, blank=True)

    # Flags
    exceeds_budget = models.BooleanField('Excede presupuesto', default=False, editable=False)

    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Solicitud de Compra'
        verbose_name_plural = 'Solicitudes de Compra'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['cost_center', 'category', 'created_at']),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.description[:50]}"

    def save(self, *args, **kwargs):
        # Generar número de solicitud si es nuevo
        if not self.request_number:
            import datetime
            today = datetime.date.today()
            count = PurchaseRequest.objects.filter(
                created_at__year=today.year,
                created_at__month=today.month
            ).count() + 1
            self.request_number = f"SOL-{today.year}{today.month:02d}-{count:04d}"

        # Auto-asignar centro de costos del solicitante
        if not self.cost_center_id:
            self.cost_center = self.requester.cost_center

        super().save(*args, **kwargs)

    def check_budget_excess(self):
        """Verifica si la solicitud excede el presupuesto disponible."""
        from autodis_compras.apps.budgets.models import Budget

        try:
            budget = Budget.objects.get(
                cost_center=self.cost_center,
                category=self.category,
                year=self.created_at.year,
                month=self.created_at.month
            )
            available = budget.get_available_amount()
            self.exceeds_budget = self.estimated_amount > available
        except Budget.DoesNotExist:
            self.exceeds_budget = True

        return self.exceeds_budget

    def can_be_edited_by(self, user):
        """Verifica si un usuario puede editar esta solicitud."""
        # Solo el solicitante puede editar
        if user != self.requester:
            return False
        # Solo si está en estado pendiente gerente
        return self.status == self.PENDIENTE_GERENTE

    def can_be_approved_by_manager(self, user):
        """Verifica si un gerente puede aprobar esta solicitud."""
        # Debe ser gerente del área
        if not user.is_manager() or user.area != self.requester.area:
            return False
        # Debe estar en estado pendiente
        return self.status == self.PENDIENTE_GERENTE

    def can_be_approved_by_finance(self, user):
        """Verifica si finanzas/dirección puede aprobar esta solicitud."""
        # Debe ser finanzas o dirección general
        if not (user.is_finance() or user.is_general_director()):
            return False
        # Debe estar aprobada por gerente
        return self.status == self.APROBADA_POR_GERENTE


class RequestComment(models.Model):
    """
    Comentarios en solicitudes de compra.
    Permite comunicación entre solicitante y aprobadores.
    """
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='comments', verbose_name='Solicitud')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='request_comments', verbose_name='Usuario')
    comment = models.TextField('Comentario')
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['created_at']

    def __str__(self):
        return f"Comentario de {self.user.get_full_name()} en {self.request.request_number}"


class RequestAttachment(models.Model):
    """
    Archivos adjuntos a solicitudes de compra.
    Máximo 10 archivos PDF de 10MB cada uno.
    """
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='attachments', verbose_name='Solicitud')
    file = models.FileField(
        'Archivo',
        upload_to=request_attachment_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text='Solo archivos PDF, máximo 10MB'
    )
    original_filename = models.CharField('Nombre original', max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_attachments', verbose_name='Subido por')
    file_size = models.IntegerField('Tamaño (bytes)', editable=False)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Archivo Adjunto'
        verbose_name_plural = 'Archivos Adjuntos'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.original_filename} - {self.request.request_number}"

    def clean(self):
        # Validar número máximo de archivos por solicitud
        if self.request.attachments.count() >= 10:
            raise ValidationError('No se pueden adjuntar más de 10 archivos por solicitud.')

        # Validar tamaño de archivo (10MB)
        if self.file.size > 10 * 1024 * 1024:
            raise ValidationError('El archivo no puede ser mayor a 10MB.')

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.original_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def get_file_size_display(self):
        """Retorna el tamaño del archivo en formato legible."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} GB"


class RequestStatusHistory(models.Model):
    """
    Historial de cambios de estado en solicitudes para trazabilidad completa.
    """
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='status_history', verbose_name='Solicitud')
    previous_status = models.CharField('Estado anterior', max_length=30, choices=PurchaseRequest.STATUS_CHOICES)
    new_status = models.CharField('Nuevo estado', max_length=30, choices=PurchaseRequest.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Modificado por')
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historial de Estados'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.request.request_number}: {self.previous_status} -> {self.new_status}"
