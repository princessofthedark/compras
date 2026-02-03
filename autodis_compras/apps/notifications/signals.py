"""
Signals para disparar notificaciones automaticas.
Se conectan a los cambios de estado en solicitudes, comentarios
y cambio de modo 'Fuera de Oficina' en usuarios.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from autodis_compras.apps.requests.models import (
    PurchaseRequest, RequestComment, RequestStatusHistory,
)
from autodis_compras.apps.users.models import User


@receiver(post_save, sender=RequestStatusHistory)
def on_status_change(sender, instance, created, **kwargs):
    """Dispara notificaciones cuando cambia el estado de una solicitud."""
    if not created:
        return

    from autodis_compras.apps.notifications.tasks import (
        notify_request_created,
        notify_manager_approved,
        notify_final_approved,
        notify_rejected,
    )

    new_status = instance.new_status

    if new_status == PurchaseRequest.PENDIENTE_GERENTE:
        notify_request_created.delay(instance.request_id)

    elif new_status == PurchaseRequest.APROBADA_POR_GERENTE:
        notify_manager_approved.delay(instance.request_id)

    elif new_status == PurchaseRequest.APROBADA:
        notify_final_approved.delay(instance.request_id)

    elif new_status in [PurchaseRequest.RECHAZADA_GERENTE, PurchaseRequest.RECHAZADA_FINANZAS]:
        notify_rejected.delay(instance.request_id)


@receiver(post_save, sender=RequestComment)
def on_comment_created(sender, instance, created, **kwargs):
    """Notifica cuando se agrega un comentario a una solicitud."""
    if not created:
        return

    from autodis_compras.apps.notifications.tasks import notify_comment_added
    notify_comment_added.delay(instance.id)


@receiver(pre_save, sender=User)
def on_out_of_office_change(sender, instance, **kwargs):
    """Detecta cuando un gerente activa 'Fuera de Oficina'."""
    if not instance.pk:
        return

    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    # Solo notificar si cambio de False a True y es gerente
    if not old_user.is_out_of_office and instance.is_out_of_office and instance.is_manager():
        from autodis_compras.apps.notifications.tasks import notify_out_of_office
        notify_out_of_office.delay(instance.pk)
