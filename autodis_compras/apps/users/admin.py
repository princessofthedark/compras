"""
Configuración del panel de administración para usuarios.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Area, Location, CostCenter


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'area', 'location', 'is_active']
    list_filter = ['area', 'location', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['area', 'location']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'area', 'is_active', 'is_out_of_office']
    list_filter = ['role', 'area', 'location', 'is_active', 'is_out_of_office', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering = ['email']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Información Organizacional', {'fields': ('role', 'area', 'location', 'cost_center', 'is_out_of_office')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role', 'area', 'location', 'cost_center'),
        }),
    )

    autocomplete_fields = ['area', 'location', 'cost_center']
