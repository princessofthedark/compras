"""
Configuración del panel de administración para notificaciones.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import EmailNotification


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'recipient', 'request', 'sent_display', 'sent_at', 'created_at']
    list_filter = ['notification_type', 'sent', 'created_at']
    search_fields = ['recipient__email', 'request__request_number', 'subject']
    readonly_fields = ['notification_type', 'recipient', 'request', 'subject', 'message', 'sent', 'sent_at', 'error_message', 'created_at']
    date_hierarchy = 'created_at'

    def sent_display(self, obj):
        if obj.sent:
            return format_html('<span style="color: green; font-weight: bold;">✓ Enviado</span>')
        elif obj.error_message:
            return format_html('<span style="color: red; font-weight: bold;">✗ Error</span>')
        return format_html('<span style="color: orange;">Pendiente</span>')
    sent_display.short_description = 'Estado'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
