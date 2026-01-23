"""
Configuración del panel de administración para solicitudes.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import PurchaseRequest, RequestComment, RequestAttachment, RequestStatusHistory


class RequestCommentInline(admin.TabularInline):
    model = RequestComment
    extra = 0
    readonly_fields = ['user', 'comment', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class RequestAttachmentInline(admin.TabularInline):
    model = RequestAttachment
    extra = 0
    readonly_fields = ['file', 'original_filename', 'uploaded_by', 'file_size', 'created_at']
    can_delete = True


class RequestStatusHistoryInline(admin.TabularInline):
    model = RequestStatusHistory
    extra = 0
    readonly_fields = ['previous_status', 'new_status', 'changed_by', 'notes', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_number',
        'requester',
        'cost_center',
        'category',
        'estimated_amount',
        'status_display',
        'urgency',
        'exceeds_budget_display',
        'created_at'
    ]
    list_filter = [
        'status',
        'urgency',
        'exceeds_budget',
        'cost_center__area',
        'category',
        'created_at'
    ]
    search_fields = [
        'request_number',
        'requester__first_name',
        'requester__last_name',
        'requester__email',
        'description'
    ]
    readonly_fields = [
        'request_number',
        'exceeds_budget',
        'created_at',
        'updated_at',
        'manager_approved_at',
        'final_approved_at',
        'rejected_at'
    ]
    autocomplete_fields = ['requester', 'cost_center', 'category', 'items']
    date_hierarchy = 'created_at'
    inlines = [RequestCommentInline, RequestAttachmentInline, RequestStatusHistoryInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('request_number', 'requester', 'cost_center', 'category', 'items', 'status')
        }),
        ('Detalles de la Solicitud', {
            'fields': (
                'description',
                'suggested_supplier',
                'estimated_amount',
                'required_date',
                'justification',
                'urgency'
            )
        }),
        ('Control Presupuestal', {
            'fields': ('exceeds_budget', 'budget_excess_justification')
        }),
        ('Aprobaciones', {
            'fields': (
                'manager_approved_at',
                'manager_approved_by',
                'final_approved_at',
                'final_approved_by'
            )
        }),
        ('Rechazo', {
            'fields': ('rejection_reason', 'rejected_at', 'rejected_by'),
            'classes': ('collapse',)
        }),
        ('Seguimiento de Compra', {
            'fields': (
                'purchase_date',
                'actual_supplier',
                'actual_amount',
                'invoice_number'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        colors = {
            PurchaseRequest.BORRADOR: 'gray',
            PurchaseRequest.PENDIENTE_GERENTE: 'orange',
            PurchaseRequest.APROBADA_POR_GERENTE: 'blue',
            PurchaseRequest.APROBADA: 'green',
            PurchaseRequest.EN_PROCESO: 'purple',
            PurchaseRequest.COMPRADA: 'darkgreen',
            PurchaseRequest.COMPLETADA: 'darkblue',
            PurchaseRequest.RECHAZADA_GERENTE: 'red',
            PurchaseRequest.RECHAZADA_FINANZAS: 'darkred',
            PurchaseRequest.CANCELADA: 'black',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Estado'

    def exceeds_budget_display(self, obj):
        if obj.exceeds_budget:
            return format_html('<span style="color: red; font-weight: bold;">SÍ</span>')
        return format_html('<span style="color: green;">No</span>')
    exceeds_budget_display.short_description = 'Excede Presupuesto'


@admin.register(RequestComment)
class RequestCommentAdmin(admin.ModelAdmin):
    list_display = ['request', 'user', 'comment_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['request__request_number', 'user__email', 'comment']
    readonly_fields = ['request', 'user', 'comment', 'created_at']
    date_hierarchy = 'created_at'

    def comment_preview(self, obj):
        return obj.comment[:100] + '...' if len(obj.comment) > 100 else obj.comment
    comment_preview.short_description = 'Comentario'

    def has_add_permission(self, request):
        return False


@admin.register(RequestAttachment)
class RequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ['request', 'original_filename', 'file_size_display', 'uploaded_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['request__request_number', 'original_filename', 'uploaded_by__email']
    readonly_fields = ['request', 'original_filename', 'file_size', 'uploaded_by', 'created_at']
    date_hierarchy = 'created_at'

    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'Tamaño'


@admin.register(RequestStatusHistory)
class RequestStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['request', 'previous_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['request__request_number', 'changed_by__email']
    readonly_fields = ['request', 'previous_status', 'new_status', 'changed_by', 'notes', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
