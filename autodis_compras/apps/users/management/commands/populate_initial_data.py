"""
Comando para poblar datos iniciales del sistema AUTODIS.
Áreas, Ubicaciones, Centros de Costos y Categorías según el PDF de especificaciones.
"""

from django.core.management.base import BaseCommand
from autodis_compras.apps.users.models import Area, Location, CostCenter
from autodis_compras.apps.budgets.models import Category


class Command(BaseCommand):
    help = 'Poblar datos iniciales (Áreas, Ubicaciones, Centros de Costos, Categorías)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando población de datos iniciales...'))

        # Crear Áreas
        self.stdout.write('Creando Áreas...')
        areas_data = [
            {'name': Area.OPERACIONES, 'description': 'Área de Operaciones (GDL, CUL, PVR)'},
            {'name': Area.COMERCIAL, 'description': 'Área Comercial (Ventas Norte, Sur, Ecommerce)'},
            {'name': Area.ADMINISTRACION, 'description': 'Área de Administración'},
            {'name': Area.FINANZAS, 'description': 'Área de Finanzas'},
            {'name': Area.PERSONAS_COMUNICACION, 'description': 'Personas y Comunicación (incluye Sistemas)'},
        ]
        for area_data in areas_data:
            area, created = Area.objects.get_or_create(
                name=area_data['name'],
                defaults={'description': area_data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Área creada: {area.get_name_display()}'))
            else:
                self.stdout.write(f'  - Área ya existe: {area.get_name_display()}')

        # Crear Ubicaciones
        self.stdout.write('\nCreando Ubicaciones...')
        locations_data = [
            Location.GUADALAJARA,
            Location.CULIACAN,
            Location.PUERTO_VALLARTA,
            Location.OFICINAS_CENTRALES,
        ]
        for location_name in locations_data:
            location, created = Location.objects.get_or_create(name=location_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Ubicación creada: {location.get_name_display()}'))
            else:
                self.stdout.write(f'  - Ubicación ya existe: {location.get_name_display()}')

        # Crear Centros de Costos
        self.stdout.write('\nCreando Centros de Costos...')
        cost_centers_data = [
            {'code': 'OPERACIONES-GDL', 'name': 'Operaciones Guadalajara', 'area': Area.OPERACIONES, 'location': Location.GUADALAJARA},
            {'code': 'OPERACIONES-CUL', 'name': 'Operaciones Culiacán', 'area': Area.OPERACIONES, 'location': Location.CULIACAN},
            {'code': 'OPERACIONES-PVR', 'name': 'Operaciones Puerto Vallarta', 'area': Area.OPERACIONES, 'location': Location.PUERTO_VALLARTA},
            {'code': 'COMERCIAL-VENTAS-NORTE', 'name': 'Comercial Ventas Norte', 'area': Area.COMERCIAL, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'COMERCIAL-VENTAS-SUR', 'name': 'Comercial Ventas Sur', 'area': Area.COMERCIAL, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'COMERCIAL-ECOMMERCE', 'name': 'Comercial Ecommerce', 'area': Area.COMERCIAL, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'ADMINISTRACION', 'name': 'Administración', 'area': Area.ADMINISTRACION, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'FINANZAS', 'name': 'Finanzas', 'area': Area.FINANZAS, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'COMUNICACION', 'name': 'Comunicación', 'area': Area.PERSONAS_COMUNICACION, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'SISTEMAS', 'name': 'Sistemas', 'area': Area.PERSONAS_COMUNICACION, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'FISCAL-JURIDICO', 'name': 'Fiscal y Jurídico', 'area': Area.ADMINISTRACION, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'DIRECCION-GENERAL', 'name': 'Dirección General', 'area': Area.ADMINISTRACION, 'location': Location.OFICINAS_CENTRALES},
        ]

        for cc_data in cost_centers_data:
            area = Area.objects.get(name=cc_data['area'])
            location = Location.objects.get(name=cc_data['location'])

            cc, created = CostCenter.objects.get_or_create(
                code=cc_data['code'],
                defaults={
                    'name': cc_data['name'],
                    'area': area,
                    'location': location,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Centro de Costos creado: {cc.code}'))
            else:
                self.stdout.write(f'  - Centro de Costos ya existe: {cc.code}')

        # Crear Categorías
        self.stdout.write('\nCreando Categorías...')
        categories_data = [
            {'code': Category.PAPELERIA, 'name': 'Papelería', 'description': 'Artículos de oficina y papelería'},
            {'code': Category.LIMPIEZA, 'name': 'Limpieza', 'description': 'Productos y servicios de limpieza'},
            {'code': Category.MANTENIMIENTO_MOTOS, 'name': 'Mantenimiento Motos', 'description': 'Mantenimiento de motocicletas'},
            {'code': Category.MANTENIMIENTO_AUTOMOVILES, 'name': 'Mantenimiento Automóviles', 'description': 'Mantenimiento de automóviles'},
            {'code': Category.MANTENIMIENTO_BODEGAS, 'name': 'Mantenimiento Bodegas', 'description': 'Mantenimiento de instalaciones'},
            {'code': Category.VIATICOS, 'name': 'Viáticos', 'description': 'Gastos de viaje y viáticos'},
            {'code': Category.SEGURIDAD_HIGIENE, 'name': 'Seguridad e Higiene', 'description': 'Equipos y productos de seguridad'},
            {'code': Category.PUBLICIDAD_EVENTOS, 'name': 'Publicidad y Eventos', 'description': 'Marketing, publicidad y eventos'},
            {'code': Category.CONSUMIBLES, 'name': 'Consumibles', 'description': 'Consumibles varios'},
            {'code': Category.COMBUSTIBLES, 'name': 'Combustibles', 'description': 'Gasolina y combustibles'},
            {'code': Category.NOMINA, 'name': 'Nómina', 'description': 'Gastos relacionados con nómina'},
            {'code': Category.IMPUESTOS, 'name': 'Impuestos', 'description': 'Impuestos y obligaciones fiscales'},
        ]

        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                code=cat_data['code'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Categoría creada: {cat.name}'))
            else:
                self.stdout.write(f'  - Categoría ya existe: {cat.name}')

        self.stdout.write('\n' + self.style.SUCCESS('✓ Población de datos iniciales completada!'))
        self.stdout.write(self.style.WARNING('\nPróximos pasos:'))
        self.stdout.write('  1. Crear un superusuario: python manage.py createsuperuser')
        self.stdout.write('  2. Acceder al panel admin y crear Items para cada categoría')
        self.stdout.write('  3. Crear usuarios del sistema con sus roles')
        self.stdout.write('  4. Cargar presupuestos iniciales')
