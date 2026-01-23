"""
Configuración del panel de administración para presupuestos.
"""

from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from .models import Category, Item, Budget, BudgetHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'items_count']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']

    def items_count(self, obj):
        return obj.items.filter(is_active=True).count()
    items_count.short_description = 'Items Activos'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['category']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['cost_center', 'category', 'year', 'month', 'amount', 'spent_display', 'available_display', 'utilization_display', 'is_closed']
    list_filter = ['year', 'month', 'is_closed', 'cost_center__area', 'category']
    search_fields = ['cost_center__code', 'cost_center__name', 'category__name']
    readonly_fields = ['created_at', 'updated_at', 'spent_display', 'available_display', 'utilization_display']
    autocomplete_fields = ['cost_center', 'category']
    date_hierarchy = 'created_at'

    def spent_display(self, obj):
        spent = obj.get_spent_amount()
        color = 'red' if obj.is_exceeded() else 'green'
        return format_html('<span style="color: {};">${:,.2f}</span>', color, spent)
    spent_display.short_description = 'Gastado'

    def available_display(self, obj):
        available = obj.get_available_amount()
        color = 'red' if available < 0 else 'green'
        return format_html('<span style="color: {};">${:,.2f}</span>', color, available)
    available_display.short_description = 'Disponible'

    def utilization_display(self, obj):
        utilization = obj.get_utilization_percentage()
        if utilization < 70:
            color = 'green'
        elif utilization < 90:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, utilization)
    utilization_display.short_description = 'Utilización'


@admin.register(BudgetHistory)
class BudgetHistoryAdmin(admin.ModelAdmin):
    list_display = ['budget', 'previous_amount', 'new_amount', 'changed_by', 'created_at']
    list_filter = ['budget__year', 'budget__month', 'changed_by']
    search_fields = ['budget__cost_center__code', 'budget__category__name']
    readonly_fields = ['budget', 'previous_amount', 'new_amount', 'changed_by', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
