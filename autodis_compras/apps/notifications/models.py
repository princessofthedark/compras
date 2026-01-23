"""
Modelos para el sistema de notificaciones por correo electrónico.
"""

from django.db import models
from autodis_compras.apps.users.models import User
from autodis_compras.apps.requests.models import PurchaseRequest


class EmailNotification(models.Model):
    """
    Registro de notificaciones por email enviadas.
    """
    SOLICITUD_CREADA = 'SOLICITUD_CREADA'
    APROBADA_GERENTE = 'APROBADA_GERENTE'
    APROBADA_FINAL = 'APROBADA_FINAL'
    RECHAZADA = 'RECHAZADA'
    COMENTARIO = 'COMENTARIO'
    FUERA_OFICINA = 'FUERA_OFICINA'

    TYPE_CHOICES = [
        (SOLICITUD_CREADA, 'Solicitud creada'),
        (APROBADA_GERENTE, 'Aprobada por gerente'),
        (APROBADA_FINAL, 'Aprobación final'),
        (RECHAZADA, 'Rechazada'),
        (COMENTARIO, 'Comentario agregado'),
        (FUERA_OFICINA, 'Fuera de oficina activado'),
    ]

    notification_type = models.CharField('Tipo', max_length=30, choices=TYPE_CHOICES)
    recipient = models.ForeignKey(User, on_delete=models.PROTECT, related_name='received_notifications', verbose_name='Destinatario')
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='notifications', verbose_name='Solicitud', null=True, blank=True)
    subject = models.CharField('Asunto', max_length=255)
    message = models.TextField('Mensaje')
    sent = models.BooleanField('Enviado', default=False)
    sent_at = models.DateTimeField('Enviado', null=True, blank=True)
    error_message = models.TextField('Error', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación por Email'
        verbose_name_plural = 'Notificaciones por Email'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} -> {self.recipient.email}"
