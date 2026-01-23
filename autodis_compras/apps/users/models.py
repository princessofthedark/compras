"""
Modelos para la gestión de usuarios, áreas y centros de costos.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class Area(models.Model):
    """
    Áreas operativas de AUTODIS.
    5 áreas principales: Operaciones, Comercial, Administración, Finanzas, Personas y Comunicación
    """
    OPERACIONES = 'OPERACIONES'
    COMERCIAL = 'COMERCIAL'
    ADMINISTRACION = 'ADMINISTRACION'
    FINANZAS = 'FINANZAS'
    PERSONAS_COMUNICACION = 'PERSONAS_COMUNICACION'

    AREA_CHOICES = [
        (OPERACIONES, 'Operaciones'),
        (COMERCIAL, 'Comercial'),
        (ADMINISTRACION, 'Administración'),
        (FINANZAS, 'Finanzas'),
        (PERSONAS_COMUNICACION, 'Personas y Comunicación'),
    ]

    name = models.CharField('Nombre', max_length=50, choices=AREA_CHOICES, unique=True)
    description = models.TextField('Descripción', blank=True)
    is_active = models.BooleanField('Activa', default=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class Location(models.Model):
    """
    Ubicaciones geográficas de AUTODIS.
    3 ubicaciones: Guadalajara, Culiacán, Puerto Vallarta
    """
    GUADALAJARA = 'GUADALAJARA'
    CULIACAN = 'CULIACAN'
    PUERTO_VALLARTA = 'PUERTO_VALLARTA'
    OFICINAS_CENTRALES = 'OFICINAS_CENTRALES'

    LOCATION_CHOICES = [
        (GUADALAJARA, 'Guadalajara'),
        (CULIACAN, 'Culiacán'),
        (PUERTO_VALLARTA, 'Puerto Vallarta'),
        (OFICINAS_CENTRALES, 'Oficinas Centrales'),
    ]

    name = models.CharField('Nombre', max_length=50, choices=LOCATION_CHOICES, unique=True)
    is_active = models.BooleanField('Activa', default=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class CostCenter(models.Model):
    """
    Centros de costos de AUTODIS.
    12 centros de costos para control presupuestal detallado.
    """
    code = models.CharField('Código', max_length=50, unique=True)
    name = models.CharField('Nombre', max_length=200)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='cost_centers', verbose_name='Área')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='cost_centers', verbose_name='Ubicación', null=True, blank=True)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Centro de Costos'
        verbose_name_plural = 'Centros de Costos'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class User(AbstractUser):
    """
    Usuario personalizado del sistema con roles y permisos específicos.
    Roles: Empleado, Gerente, Finanzas, Dirección General
    """
    EMPLEADO = 'EMPLEADO'
    GERENTE = 'GERENTE'
    FINANZAS = 'FINANZAS'
    DIRECCION_GENERAL = 'DIRECCION_GENERAL'

    ROLE_CHOICES = [
        (EMPLEADO, 'Empleado'),
        (GERENTE, 'Gerente de Área'),
        (FINANZAS, 'Finanzas'),
        (DIRECCION_GENERAL, 'Dirección General'),
    ]

    email = models.EmailField('Correo electrónico', unique=True)
    role = models.CharField('Rol', max_length=20, choices=ROLE_CHOICES, default=EMPLEADO)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='users', verbose_name='Área')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='users', verbose_name='Ubicación')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, related_name='users', verbose_name='Centro de Costos')
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    is_out_of_office = models.BooleanField('Fuera de Oficina', default=False, help_text='Activa para delegar aprobaciones temporalmente')
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    # Override username field to use email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Ensure email is lowercase
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def is_manager(self):
        """Verifica si el usuario es gerente de área."""
        return self.role == self.GERENTE

    def is_finance(self):
        """Verifica si el usuario es de Finanzas."""
        return self.role == self.FINANZAS

    def is_general_director(self):
        """Verifica si el usuario es Director General."""
        return self.role == self.DIRECCION_GENERAL

    def is_approver(self):
        """Verifica si el usuario puede aprobar solicitudes."""
        return self.role in [self.GERENTE, self.FINANZAS, self.DIRECCION_GENERAL]

    def can_manage_users(self):
        """Verifica si el usuario puede gestionar otros usuarios."""
        return self.role in [self.FINANZAS, self.DIRECCION_GENERAL, self.GERENTE]

    def can_manage_budgets(self):
        """Verifica si el usuario puede gestionar presupuestos."""
        return self.role in [self.FINANZAS, self.DIRECCION_GENERAL]
