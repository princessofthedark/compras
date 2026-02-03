"""
Serializers para el módulo de solicitudes de compra.
"""

from rest_framework import serializers
from .models import PurchaseRequest, RequestComment, RequestAttachment, RequestStatusHistory


class RequestStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    previous_status_display = serializers.CharField(source='get_previous_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)

    class Meta:
        model = RequestStatusHistory
        fields = [
            'id', 'previous_status', 'previous_status_display',
            'new_status', 'new_status_display',
            'changed_by', 'changed_by_name', 'notes', 'created_at',
        ]
        read_only_fields = ['created_at']


class RequestCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = RequestComment
        fields = ['id', 'request', 'user', 'user_name', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']


class RequestAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)

    class Meta:
        model = RequestAttachment
        fields = [
            'id', 'request', 'file', 'original_filename', 'uploaded_by',
            'uploaded_by_name', 'file_size', 'file_size_display', 'created_at',
        ]
        read_only_fields = ['uploaded_by', 'original_filename', 'file_size', 'created_at']


class PurchaseRequestListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados."""
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    cost_center_name = serializers.CharField(source='cost_center.__str__', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'request_number', 'requester', 'requester_name',
            'cost_center', 'cost_center_name', 'category', 'category_name',
            'description', 'estimated_amount', 'required_date',
            'urgency', 'urgency_display', 'status', 'status_display',
            'exceeds_budget', 'created_at', 'updated_at',
        ]
        read_only_fields = ['request_number', 'exceeds_budget', 'created_at', 'updated_at']


class PurchaseRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para vista de detalle."""
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    cost_center_name = serializers.CharField(source='cost_center.__str__', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    manager_approved_by_name = serializers.CharField(
        source='manager_approved_by.get_full_name', read_only=True, default=None
    )
    final_approved_by_name = serializers.CharField(
        source='final_approved_by.get_full_name', read_only=True, default=None
    )
    rejected_by_name = serializers.CharField(
        source='rejected_by.get_full_name', read_only=True, default=None
    )
    comments = RequestCommentSerializer(many=True, read_only=True)
    attachments = RequestAttachmentSerializer(many=True, read_only=True)
    status_history = RequestStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'request_number', 'requester', 'requester_name',
            'cost_center', 'cost_center_name', 'category', 'category_name',
            'items', 'description', 'suggested_supplier',
            'estimated_amount', 'required_date', 'justification',
            'budget_excess_justification', 'urgency', 'urgency_display',
            'status', 'status_display', 'exceeds_budget',
            'manager_approved_at', 'manager_approved_by', 'manager_approved_by_name',
            'final_approved_at', 'final_approved_by', 'final_approved_by_name',
            'rejection_reason', 'rejected_at', 'rejected_by', 'rejected_by_name',
            'purchase_date', 'actual_supplier', 'actual_amount', 'invoice_number',
            'comments', 'attachments', 'status_history',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'request_number', 'exceeds_budget',
            'manager_approved_at', 'manager_approved_by',
            'final_approved_at', 'final_approved_by',
            'rejected_at', 'rejected_by',
            'created_at', 'updated_at',
        ]


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear/editar solicitudes."""

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'request_number', 'category', 'items', 'description',
            'suggested_supplier', 'estimated_amount', 'required_date',
            'justification', 'budget_excess_justification', 'urgency',
        ]
        read_only_fields = ['request_number']

    def create(self, validated_data):
        items = validated_data.pop('items', [])
        user = self.context['request'].user
        validated_data['requester'] = user
        validated_data['cost_center'] = user.cost_center
        validated_data['status'] = PurchaseRequest.PENDIENTE_GERENTE
        purchase_request = PurchaseRequest.objects.create(**validated_data)
        if items:
            purchase_request.items.set(items)
        purchase_request.check_budget_excess()
        purchase_request.save()
        return purchase_request
