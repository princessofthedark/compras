"""
Tareas Celery para el envio de notificaciones por correo electronico.
Segun la especificacion del PDF, se envian notificaciones en los siguientes eventos:
- Solicitud creada -> Gerente del area
- Aprobada por gerente -> Finanzas Y Direccion General
- Aprobada finalmente -> Solicitante y gerente
- Rechazada -> Solicitante y gerente con motivo
- Comentario agregado -> Todos los involucrados
- Fuera de oficina activado -> Finanzas y Direccion General
"""

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, notification_id):
    """Envia un email de notificacion y actualiza su estado."""
    from autodis_compras.apps.notifications.models import EmailNotification

    try:
        notification = EmailNotification.objects.get(id=notification_id)
        if notification.sent:
            return f'Notificacion {notification_id} ya fue enviada'

        send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )

        notification.sent = True
        notification.sent_at = timezone.now()
        notification.save(update_fields=['sent', 'sent_at'])

        logger.info(f'Notificacion {notification_id} enviada a {notification.recipient.email}')
        return f'Enviada a {notification.recipient.email}'

    except EmailNotification.DoesNotExist:
        logger.error(f'Notificacion {notification_id} no existe')
    except Exception as exc:
        logger.error(f'Error enviando notificacion {notification_id}: {exc}')
        try:
            notification = EmailNotification.objects.get(id=notification_id)
            notification.error_message = str(exc)
            notification.save(update_fields=['error_message'])
        except EmailNotification.DoesNotExist:
            pass
        raise self.retry(exc=exc)


@shared_task
def notify_request_created(request_id):
    """Notifica al gerente del area que se creo una nueva solicitud."""
    from autodis_compras.apps.requests.models import PurchaseRequest
    from autodis_compras.apps.notifications.models import EmailNotification
    from autodis_compras.apps.users.models import User

    try:
        purchase_request = PurchaseRequest.objects.select_related(
            'requester', 'requester__area', 'category', 'cost_center'
        ).get(id=request_id)

        requester = purchase_request.requester
        area = requester.area

        # Buscar gerente del area
        manager = User.objects.filter(
            area=area,
            role=User.GERENTE,
            is_active=True,
        ).first()

        # Si gerente esta fuera de oficina o no existe, notificar a Finanzas/DG
        if manager and not manager.is_out_of_office:
            recipients = [manager]
        else:
            recipients = list(User.objects.filter(
                role__in=[User.FINANZAS, User.DIRECCION_GENERAL],
                is_active=True,
            ))

        budget_warning = ''
        if purchase_request.exceeds_budget:
            budget_warning = '\n** ALERTA: Esta solicitud EXCEDE el presupuesto disponible **\n'

        for recipient in recipients:
            subject = f'Nueva solicitud de compra: {purchase_request.request_number}'
            message = (
                f'Se ha creado una nueva solicitud de compra que requiere su aprobacion.\n\n'
                f'Numero: {purchase_request.request_number}\n'
                f'Solicitante: {requester.get_full_name()}\n'
                f'Categoria: {purchase_request.category.name}\n'
                f'Descripcion: {purchase_request.description}\n'
                f'Monto estimado: ${purchase_request.estimated_amount:,.2f} MXN\n'
                f'Urgencia: {purchase_request.get_urgency_display()}\n'
                f'Fecha requerida: {purchase_request.required_date}\n'
                f'{budget_warning}'
            )

            notification = EmailNotification.objects.create(
                notification_type=EmailNotification.SOLICITUD_CREADA,
                recipient=recipient,
                request=purchase_request,
                subject=subject,
                message=message,
            )
            send_notification_email.delay(notification.id)

    except PurchaseRequest.DoesNotExist:
        logger.error(f'Solicitud {request_id} no existe')


@shared_task
def notify_manager_approved(request_id):
    """Notifica a Finanzas Y Direccion General que un gerente aprobo la solicitud."""
    from autodis_compras.apps.requests.models import PurchaseRequest
    from autodis_compras.apps.notifications.models import EmailNotification
    from autodis_compras.apps.users.models import User

    try:
        purchase_request = PurchaseRequest.objects.select_related(
            'requester', 'requester__area', 'category', 'manager_approved_by'
        ).get(id=request_id)

        recipients = User.objects.filter(
            role__in=[User.FINANZAS, User.DIRECCION_GENERAL],
            is_active=True,
        )

        budget_warning = ''
        if purchase_request.exceeds_budget:
            budget_warning = (
                f'\n** ALERTA: Esta solicitud EXCEDE el presupuesto disponible **\n'
                f'Justificacion de exceso: {purchase_request.budget_excess_justification}\n'
            )

        for recipient in recipients:
            subject = f'Solicitud aprobada por gerente: {purchase_request.request_number}'
            message = (
                f'La siguiente solicitud ha sido aprobada por el gerente y requiere su aprobacion final.\n\n'
                f'Numero: {purchase_request.request_number}\n'
                f'Solicitante: {purchase_request.requester.get_full_name()}\n'
                f'Area: {purchase_request.requester.area.get_name_display()}\n'
                f'Aprobado por: {purchase_request.manager_approved_by.get_full_name()}\n'
                f'Categoria: {purchase_request.category.name}\n'
                f'Descripcion: {purchase_request.description}\n'
                f'Monto estimado: ${purchase_request.estimated_amount:,.2f} MXN\n'
                f'{budget_warning}'
            )

            notification = EmailNotification.objects.create(
                notification_type=EmailNotification.APROBADA_GERENTE,
                recipient=recipient,
                request=purchase_request,
                subject=subject,
                message=message,
            )
            send_notification_email.delay(notification.id)

    except PurchaseRequest.DoesNotExist:
        logger.error(f'Solicitud {request_id} no existe')


@shared_task
def notify_final_approved(request_id):
    """Notifica al solicitante y al gerente que la solicitud fue aprobada finalmente."""
    from autodis_compras.apps.requests.models import PurchaseRequest
    from autodis_compras.apps.notifications.models import EmailNotification
    from autodis_compras.apps.users.models import User

    try:
        purchase_request = PurchaseRequest.objects.select_related(
            'requester', 'requester__area', 'category', 'final_approved_by'
        ).get(id=request_id)

        # Notificar al solicitante
        recipients = [purchase_request.requester]

        # Notificar al gerente del area
        manager = User.objects.filter(
            area=purchase_request.requester.area,
            role=User.GERENTE,
            is_active=True,
        ).first()
        if manager:
            recipients.append(manager)

        for recipient in recipients:
            subject = f'Solicitud APROBADA: {purchase_request.request_number}'
            message = (
                f'Su solicitud de compra ha sido aprobada y puede proceder con la compra.\n\n'
                f'Numero: {purchase_request.request_number}\n'
                f'Descripcion: {purchase_request.description}\n'
                f'Monto aprobado: ${purchase_request.estimated_amount:,.2f} MXN\n'
                f'Aprobado por: {purchase_request.final_approved_by.get_full_name()}\n'
            )

            notification = EmailNotification.objects.create(
                notification_type=EmailNotification.APROBADA_FINAL,
                recipient=recipient,
                request=purchase_request,
                subject=subject,
                message=message,
            )
            send_notification_email.delay(notification.id)

    except PurchaseRequest.DoesNotExist:
        logger.error(f'Solicitud {request_id} no existe')


@shared_task
def notify_rejected(request_id):
    """Notifica al solicitante y al gerente que la solicitud fue rechazada."""
    from autodis_compras.apps.requests.models import PurchaseRequest
    from autodis_compras.apps.notifications.models import EmailNotification
    from autodis_compras.apps.users.models import User

    try:
        purchase_request = PurchaseRequest.objects.select_related(
            'requester', 'requester__area', 'rejected_by'
        ).get(id=request_id)

        recipients = [purchase_request.requester]

        manager = User.objects.filter(
            area=purchase_request.requester.area,
            role=User.GERENTE,
            is_active=True,
        ).first()
        if manager and manager != purchase_request.rejected_by:
            recipients.append(manager)

        for recipient in recipients:
            subject = f'Solicitud RECHAZADA: {purchase_request.request_number}'
            message = (
                f'La solicitud de compra ha sido rechazada.\n\n'
                f'Numero: {purchase_request.request_number}\n'
                f'Descripcion: {purchase_request.description}\n'
                f'Rechazada por: {purchase_request.rejected_by.get_full_name()}\n'
                f'Motivo: {purchase_request.rejection_reason}\n'
            )

            notification = EmailNotification.objects.create(
                notification_type=EmailNotification.RECHAZADA,
                recipient=recipient,
                request=purchase_request,
                subject=subject,
                message=message,
            )
            send_notification_email.delay(notification.id)

    except PurchaseRequest.DoesNotExist:
        logger.error(f'Solicitud {request_id} no existe')


@shared_task
def notify_comment_added(comment_id):
    """Notifica a todos los involucrados que se agrego un comentario."""
    from autodis_compras.apps.requests.models import RequestComment
    from autodis_compras.apps.notifications.models import EmailNotification
    from autodis_compras.apps.users.models import User

    try:
        comment = RequestComment.objects.select_related(
            'request', 'request__requester', 'request__requester__area', 'user'
        ).get(id=comment_id)

        purchase_request = comment.request
        commenter = comment.user

        # Reunir todos los involucrados (sin duplicados, excluyendo al autor)
        involved = set()
        involved.add(purchase_request.requester_id)

        # Gerente del area
        manager = User.objects.filter(
            area=purchase_request.requester.area,
            role=User.GERENTE,
            is_active=True,
        ).first()
        if manager:
            involved.add(manager.id)

        # Si ya tiene aprobador final
        if purchase_request.final_approved_by_id:
            involved.add(purchase_request.final_approved_by_id)
        if purchase_request.manager_approved_by_id:
            involved.add(purchase_request.manager_approved_by_id)

        # Excluir al autor del comentario
        involved.discard(commenter.id)

        recipients = User.objects.filter(id__in=involved, is_active=True)

        for recipient in recipients:
            subject = f'Nuevo comentario en solicitud {purchase_request.request_number}'
            message = (
                f'{commenter.get_full_name()} agrego un comentario a la solicitud.\n\n'
                f'Solicitud: {purchase_request.request_number}\n'
                f'Comentario: {comment.comment}\n'
            )

            notification = EmailNotification.objects.create(
                notification_type=EmailNotification.COMENTARIO,
                recipient=recipient,
                request=purchase_request,
                subject=subject,
                message=message,
            )
            send_notification_email.delay(notification.id)

    except RequestComment.DoesNotExist:
        logger.error(f'Comentario {comment_id} no existe')


@shared_task
def notify_out_of_office(user_id):
    """Notifica a Finanzas y Direccion General que un gerente activo fuera de oficina."""
    from autodis_compras.apps.notifications.models import EmailNotification
    from autodis_compras.apps.users.models import User

    try:
        manager = User.objects.select_related('area').get(id=user_id)

        recipients = User.objects.filter(
            role__in=[User.FINANZAS, User.DIRECCION_GENERAL],
            is_active=True,
        )

        for recipient in recipients:
            subject = f'Gerente Fuera de Oficina: {manager.get_full_name()}'
            message = (
                f'{manager.get_full_name()} ha activado el modo "Fuera de Oficina".\n\n'
                f'Area: {manager.area.get_name_display()}\n\n'
                f'Las solicitudes de su area seran enviadas directamente '
                f'a Finanzas y Direccion General para aprobacion.\n'
            )

            notification = EmailNotification.objects.create(
                notification_type=EmailNotification.FUERA_OFICINA,
                recipient=recipient,
                subject=subject,
                message=message,
            )
            send_notification_email.delay(notification.id)

    except User.DoesNotExist:
        logger.error(f'Usuario {user_id} no existe')
