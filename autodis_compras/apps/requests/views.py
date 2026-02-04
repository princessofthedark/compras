"""
ViewSets para el módulo de solicitudes de compra.
"""

from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import PurchaseRequest, RequestComment, RequestAttachment, RequestStatusHistory
from .serializers import (
    PurchaseRequestListSerializer,
    PurchaseRequestDetailSerializer,
    PurchaseRequestCreateSerializer,
    RequestCommentSerializer,
    RequestAttachmentSerializer,
    RequestStatusHistorySerializer,
)


@extend_schema_view(
    list=extend_schema(tags=['Solicitudes']), retrieve=extend_schema(tags=['Solicitudes']),
    create=extend_schema(tags=['Solicitudes']), update=extend_schema(tags=['Solicitudes']),
    partial_update=extend_schema(tags=['Solicitudes']), destroy=extend_schema(tags=['Solicitudes']),
    submit=extend_schema(tags=['Solicitudes']), approve_manager=extend_schema(tags=['Solicitudes']),
    approve_final=extend_schema(tags=['Solicitudes']), reject=extend_schema(tags=['Solicitudes']),
    cancel=extend_schema(tags=['Solicitudes']), mark_in_process=extend_schema(tags=['Solicitudes']),
    mark_purchased=extend_schema(tags=['Solicitudes']), mark_completed=extend_schema(tags=['Solicitudes']),
)
class PurchaseRequestViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequest.objects.select_related(
        'requester', 'cost_center', 'category',
        'manager_approved_by', 'final_approved_by', 'rejected_by',
    ).prefetch_related('items', 'comments', 'attachments', 'status_history').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'urgency', 'category', 'cost_center', 'requester', 'exceeds_budget']
    search_fields = ['request_number', 'description', 'suggested_supplier']
    ordering_fields = ['created_at', 'required_date', 'estimated_amount', 'status']

    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseRequestCreateSerializer
        if self.action == 'list':
            return PurchaseRequestListSerializer
        return PurchaseRequestDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_finance() or user.is_general_director():
            return self.queryset
        if user.is_manager():
            return self.queryset.filter(requester__area=user.area)
        return self.queryset.filter(requester=user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Enviar borrador a aprobación de gerente."""
        purchase_request = self.get_object()
        if purchase_request.status != PurchaseRequest.BORRADOR:
            return Response(
                {'error': 'Solo se pueden enviar solicitudes en borrador.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if purchase_request.requester != request.user:
            return Response(
                {'error': 'Solo el solicitante puede enviar la solicitud.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        old_status = purchase_request.status
        purchase_request.status = PurchaseRequest.PENDIENTE_GERENTE
        purchase_request.check_budget_excess()
        purchase_request.save()
        RequestStatusHistory.objects.create(
            request=purchase_request,
            previous_status=old_status,
            new_status=purchase_request.status,
            changed_by=request.user,
            notes='Solicitud enviada a aprobación.',
        )
        return Response(PurchaseRequestDetailSerializer(purchase_request).data)

    @action(detail=True, methods=['post'])
    def approve_manager(self, request, pk=None):
        """Aprobación por gerente de área."""
        purchase_request = self.get_object()
        if not purchase_request.can_be_approved_by_manager(request.user):
            return Response(
                {'error': 'No tiene permisos para aprobar esta solicitud o no está en el estado correcto.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        old_status = purchase_request.status
        purchase_request.status = PurchaseRequest.APROBADA_POR_GERENTE
        purchase_request.manager_approved_by = request.user
        purchase_request.manager_approved_at = timezone.now()
        purchase_request.save()
        RequestStatusHistory.objects.create(
            request=purchase_request,
            previous_status=old_status,
            new_status=purchase_request.status,
            changed_by=request.user,
            notes=request.data.get('notes', 'Aprobada por gerente.'),
        )
        return Response(PurchaseRequestDetailSerializer(purchase_request).data)

    @action(detail=True, methods=['post'])
    def approve_final(self, request, pk=None):
        """Aprobación final por Finanzas o Dirección General."""
        purchase_request = self.get_object()
        if not purchase_request.can_be_approved_by_finance(request.user):
            return Response(
                {'error': 'No tiene permisos para aprobar esta solicitud o no está en el estado correcto.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        old_status = purchase_request.status
        purchase_request.status = PurchaseRequest.APROBADA
        purchase_request.final_approved_by = request.user
        purchase_request.final_approved_at = timezone.now()
        purchase_request.save()
        RequestStatusHistory.objects.create(
            request=purchase_request,
            previous_status=old_status,
            new_status=purchase_request.status,
            changed_by=request.user,
            notes=request.data.get('notes', 'Aprobación final.'),
        )
        return Response(PurchaseRequestDetailSerializer(purchase_request).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechazar solicitud (por gerente o finanzas)."""
        purchase_request = self.get_object()
        reason = request.data.get('reason', '')
        if not reason:
            return Response(
                {'error': 'Debe proporcionar una razón de rechazo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        old_status = purchase_request.status

        if purchase_request.status == PurchaseRequest.PENDIENTE_GERENTE and purchase_request.can_be_approved_by_manager(user):
            purchase_request.status = PurchaseRequest.RECHAZADA_GERENTE
        elif purchase_request.status == PurchaseRequest.APROBADA_POR_GERENTE and purchase_request.can_be_approved_by_finance(user):
            purchase_request.status = PurchaseRequest.RECHAZADA_FINANZAS
        else:
            return Response(
                {'error': 'No tiene permisos para rechazar esta solicitud o no está en el estado correcto.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        purchase_request.rejection_reason = reason
        purchase_request.rejected_by = user
        purchase_request.rejected_at = timezone.now()
        purchase_request.save()
        RequestStatusHistory.objects.create(
            request=purchase_request,
            previous_status=old_status,
            new_status=purchase_request.status,
            changed_by=user,
            notes=f'Rechazada: {reason}',
        )
        return Response(PurchaseRequestDetailSerializer(purchase_request).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar solicitud (solo el solicitante, en estados editables)."""
        purchase_request = self.get_object()
        if purchase_request.requester != request.user:
            return Response(
                {'error': 'Solo el solicitante puede cancelar.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        cancellable_states = [
            PurchaseRequest.BORRADOR,
            PurchaseRequest.PENDIENTE_GERENTE,
        ]
        if purchase_request.status not in cancellable_states:
            return Response(
                {'error': 'La solicitud no puede ser cancelada en su estado actual.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        old_status = purchase_request.status
        purchase_request.status = PurchaseRequest.CANCELADA
        purchase_request.save()
        RequestStatusHistory.objects.create(
            request=purchase_request,
            previous_status=old_status,
            new_status=purchase_request.status,
            changed_by=request.user,
            notes=request.data.get('notes', 'Solicitud cancelada por el solicitante.'),
        )
        return Response(PurchaseRequestDetailSerializer(purchase_request).data)

    @action(detail=True, methods=['post'])
    def mark_in_process(self, request, pk=None):
        """Marcar como en proceso de compra (Finanzas)."""
        purchase_request = self.get_object()
        if not (request.user.is_finance() or request.user.is_general_director()):
            return Response({'error': 'Solo Finanzas puede marcar en proceso.'}, status=status.HTTP_403_FORBIDDEN)
        if purchase_request.status != PurchaseRequest.APROBADA:
            return Response({'error': 'La solicitud debe estar aprobada.'}, status=status.HTTP_400_BAD_REQUEST)
        old_status = purchase_request.status
        purchase_request.status = PurchaseRequest.EN_PROCESO
        purchase_request.save()
        RequestStatusHistory.objects.create(
            request=purchase_request, previous_status=old_status,
            new_status=purchase_request.status, changed_by=request.user,
            notes='Marcada en proceso de compra.',
        )
        return Response(PurchaseRequestDetailSerializer(purchase_request).data)

    @action(detail=True, methods=['post'])
    def mark_purchased(self, request, pk=None):
        """Marcar como comprada con datos de compra."""
        purchase_request = self.get_object()
        if not (request.user.is_finance() or request.user.is_general_director()):
            return Response({'error': 'Solo Finanzas puede marcar como comprada.'}, status=status.HTTP_403_FORBIDDEN)
        if purchase_request.status != PurchaseRequest.EN_PROCESO:
            return Response({'error': 'La solicitud debe estar en proceso.'}, status=status.HTTP_400_BAD_REQUEST)
        old_status = purchase_request.status
        purchase_request.status = PurchaseRequest.COMPRADA
        purchase_request.purchase_date = request.data.get('purchase_date')
        purchase_request.actual_supplier = request.data.get('actual_supplier', '')
        purchase_request.actual_amount = request.data.get('actual_amount')
        purchase_request.invoice_number = request.data.get('invoice_number', '')
        purchase_request.save()
        RequestStatusHistory.objects.create(
            request=purchase_request, previous_status=old_status,
            new_status=purchase_request.status, changed_by=request.user,
            notes='Compra realizada.',
        )
        return Response(PurchaseRequestDetailSerializer(purchase_request).data)

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Marcar como completada."""
        purchase_request = self.get_object()
        if not (request.user.is_finance() or request.user.is_general_director()):
            return Response({'error': 'Solo Finanzas puede completar.'}, status=status.HTTP_403_FORBIDDEN)
        if purchase_request.status != PurchaseRequest.COMPRADA:
            return Response({'error': 'La solicitud debe estar comprada.'}, status=status.HTTP_400_BAD_REQUEST)
        old_status = purchase_request.status
        purchase_request.status = PurchaseRequest.COMPLETADA
        purchase_request.save()
        RequestStatusHistory.objects.create(
            request=purchase_request, previous_status=old_status,
            new_status=purchase_request.status, changed_by=request.user,
            notes='Solicitud completada.',
        )
        return Response(PurchaseRequestDetailSerializer(purchase_request).data)


@extend_schema_view(list=extend_schema(tags=['Comentarios']), retrieve=extend_schema(tags=['Comentarios']),
                     create=extend_schema(tags=['Comentarios']), update=extend_schema(tags=['Comentarios']),
                     partial_update=extend_schema(tags=['Comentarios']), destroy=extend_schema(tags=['Comentarios']))
class RequestCommentViewSet(viewsets.ModelViewSet):
    queryset = RequestComment.objects.select_related('user').all()
    serializer_class = RequestCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['request']
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(list=extend_schema(tags=['Adjuntos']), retrieve=extend_schema(tags=['Adjuntos']),
                     create=extend_schema(tags=['Adjuntos']), destroy=extend_schema(tags=['Adjuntos']))
class RequestAttachmentViewSet(viewsets.ModelViewSet):
    queryset = RequestAttachment.objects.select_related('uploaded_by').all()
    serializer_class = RequestAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['request']
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get('file')
        if file_obj and file_obj.size > 10 * 1024 * 1024:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'file': 'El archivo no puede ser mayor a 10MB.'})
        purchase_request = serializer.validated_data.get('request')
        if purchase_request and purchase_request.attachments.count() >= 10:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'file': 'No se pueden adjuntar más de 10 archivos por solicitud.'})
        serializer.save(uploaded_by=self.request.user)
