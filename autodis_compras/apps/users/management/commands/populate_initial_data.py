"""
Comando para poblar datos iniciales del sistema AUTODIS.
Áreas, Ubicaciones, Centros de Costos, Categorías e Items (228)
según el PDF de especificaciones.
"""

from django.core.management.base import BaseCommand
from autodis_compras.apps.users.models import Area, Location, CostCenter
from autodis_compras.apps.budgets.models import Category, Item


class Command(BaseCommand):
    help = 'Poblar datos iniciales (Áreas, Ubicaciones, Centros de Costos, Categorías e Items)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando poblacion de datos iniciales...'))

        # Crear Áreas
        self.stdout.write('Creando Areas...')
        areas_data = [
            {'name': Area.OPERACIONES, 'description': 'Area de Operaciones (GDL, CUL, PVR)'},
            {'name': Area.COMERCIAL, 'description': 'Area Comercial (Ventas Norte, Sur, Ecommerce)'},
            {'name': Area.ADMINISTRACION, 'description': 'Area de Administracion'},
            {'name': Area.FINANZAS, 'description': 'Area de Finanzas'},
            {'name': Area.PERSONAS_COMUNICACION, 'description': 'Personas y Comunicacion (incluye Sistemas)'},
        ]
        for area_data in areas_data:
            area, created = Area.objects.get_or_create(
                name=area_data['name'],
                defaults={'description': area_data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  + Area creada: {area.get_name_display()}'))
            else:
                self.stdout.write(f'  - Area ya existe: {area.get_name_display()}')

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
                self.stdout.write(self.style.SUCCESS(f'  + Ubicacion creada: {location.get_name_display()}'))
            else:
                self.stdout.write(f'  - Ubicacion ya existe: {location.get_name_display()}')

        # Crear Centros de Costos
        self.stdout.write('\nCreando Centros de Costos...')
        cost_centers_data = [
            {'code': 'OPERACIONES-GDL', 'name': 'Operaciones Guadalajara', 'area': Area.OPERACIONES, 'location': Location.GUADALAJARA},
            {'code': 'OPERACIONES-CUL', 'name': 'Operaciones Culiacan', 'area': Area.OPERACIONES, 'location': Location.CULIACAN},
            {'code': 'OPERACIONES-PVR', 'name': 'Operaciones Puerto Vallarta', 'area': Area.OPERACIONES, 'location': Location.PUERTO_VALLARTA},
            {'code': 'COMERCIAL-VENTAS-NORTE', 'name': 'Comercial Ventas Norte', 'area': Area.COMERCIAL, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'COMERCIAL-VENTAS-SUR', 'name': 'Comercial Ventas Sur', 'area': Area.COMERCIAL, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'COMERCIAL-ECOMMERCE', 'name': 'Comercial Ecommerce', 'area': Area.COMERCIAL, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'ADMINISTRACION', 'name': 'Administracion', 'area': Area.ADMINISTRACION, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'FINANZAS', 'name': 'Finanzas', 'area': Area.FINANZAS, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'COMUNICACION', 'name': 'Comunicacion', 'area': Area.PERSONAS_COMUNICACION, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'SISTEMAS', 'name': 'Sistemas', 'area': Area.PERSONAS_COMUNICACION, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'FISCAL-JURIDICO', 'name': 'Fiscal y Juridico', 'area': Area.ADMINISTRACION, 'location': Location.OFICINAS_CENTRALES},
            {'code': 'DIRECCION-GENERAL', 'name': 'Direccion General', 'area': Area.ADMINISTRACION, 'location': Location.OFICINAS_CENTRALES},
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
                self.stdout.write(self.style.SUCCESS(f'  + Centro de Costos creado: {cc.code}'))
            else:
                self.stdout.write(f'  - Centro de Costos ya existe: {cc.code}')

        # Crear Categorías
        self.stdout.write('\nCreando Categorias...')
        categories_data = [
            {'code': Category.PAPELERIA, 'name': 'Papeleria', 'description': 'Articulos de oficina y papeleria'},
            {'code': Category.LIMPIEZA, 'name': 'Limpieza', 'description': 'Productos y servicios de limpieza'},
            {'code': Category.MANTENIMIENTO_MOTOS, 'name': 'Mantenimiento Motos', 'description': 'Mantenimiento de motocicletas'},
            {'code': Category.MANTENIMIENTO_AUTOMOVILES, 'name': 'Mantenimiento Automoviles', 'description': 'Mantenimiento de automoviles'},
            {'code': Category.MANTENIMIENTO_BODEGAS, 'name': 'Mantenimiento Bodegas', 'description': 'Mantenimiento de instalaciones'},
            {'code': Category.VIATICOS, 'name': 'Viaticos', 'description': 'Gastos de viaje y viaticos'},
            {'code': Category.SEGURIDAD_HIGIENE, 'name': 'Seguridad e Higiene', 'description': 'Equipos y productos de seguridad'},
            {'code': Category.PUBLICIDAD_EVENTOS, 'name': 'Publicidad y Eventos', 'description': 'Marketing, publicidad y eventos'},
            {'code': Category.CONSUMIBLES, 'name': 'Consumibles', 'description': 'Consumibles varios'},
            {'code': Category.COMBUSTIBLES, 'name': 'Combustibles', 'description': 'Gasolina y combustibles'},
            {'code': Category.NOMINA, 'name': 'Nomina', 'description': 'Gastos relacionados con nomina'},
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
                self.stdout.write(self.style.SUCCESS(f'  + Categoria creada: {cat.name}'))
            else:
                self.stdout.write(f'  - Categoria ya existe: {cat.name}')

        # Crear Items (228 en total, distribuidos en 12 categorias)
        self.stdout.write('\nCreando Items (228 en total)...')
        self._create_items()

        self.stdout.write('\n' + self.style.SUCCESS('Poblacion de datos iniciales completada!'))
        self.stdout.write(self.style.WARNING('\nProximos pasos:'))
        self.stdout.write('  1. Crear un superusuario: python manage.py createsuperuser')
        self.stdout.write('  2. Crear usuarios del sistema con sus roles')
        self.stdout.write('  3. Cargar presupuestos iniciales')

    def _create_items(self):
        """Crea los 228 items distribuidos en las 12 categorias."""
        items_by_category = {
            # PAPELERIA - 50 items
            Category.PAPELERIA: [
                ('PAP-001', 'Hojas blancas carta', 'Paquete'),
                ('PAP-002', 'Hojas blancas oficio', 'Paquete'),
                ('PAP-003', 'Hojas de colores carta', 'Paquete'),
                ('PAP-004', 'Folders manila carta', 'Paquete'),
                ('PAP-005', 'Folders manila oficio', 'Paquete'),
                ('PAP-006', 'Sobres manila carta', 'Paquete'),
                ('PAP-007', 'Sobres manila oficio', 'Paquete'),
                ('PAP-008', 'Sobres blancos carta', 'Paquete'),
                ('PAP-009', 'Plumas azules', 'Caja'),
                ('PAP-010', 'Plumas negras', 'Caja'),
                ('PAP-011', 'Plumas rojas', 'Caja'),
                ('PAP-012', 'Lapices No. 2', 'Caja'),
                ('PAP-013', 'Marcadores permanentes', 'Paquete'),
                ('PAP-014', 'Marcatextos', 'Paquete'),
                ('PAP-015', 'Gomas de borrar', 'Pieza'),
                ('PAP-016', 'Sacapuntas', 'Pieza'),
                ('PAP-017', 'Tijeras', 'Pieza'),
                ('PAP-018', 'Cinta adhesiva transparente', 'Pieza'),
                ('PAP-019', 'Cinta adhesiva canela', 'Pieza'),
                ('PAP-020', 'Pegamento en barra', 'Pieza'),
                ('PAP-021', 'Pegamento liquido', 'Pieza'),
                ('PAP-022', 'Clips estandar', 'Caja'),
                ('PAP-023', 'Clips mariposa', 'Caja'),
                ('PAP-024', 'Grapas estandar', 'Caja'),
                ('PAP-025', 'Engrapadora', 'Pieza'),
                ('PAP-026', 'Perforadora 2 orificios', 'Pieza'),
                ('PAP-027', 'Post-it notas adhesivas', 'Paquete'),
                ('PAP-028', 'Post-it banderitas', 'Paquete'),
                ('PAP-029', 'Libretas profesionales rayadas', 'Pieza'),
                ('PAP-030', 'Libretas profesionales cuadro', 'Pieza'),
                ('PAP-031', 'Carpetas argolla 1 pulgada', 'Pieza'),
                ('PAP-032', 'Carpetas argolla 2 pulgadas', 'Pieza'),
                ('PAP-033', 'Carpetas argolla 3 pulgadas', 'Pieza'),
                ('PAP-034', 'Protectores de hojas', 'Paquete'),
                ('PAP-035', 'Separadores de colores', 'Paquete'),
                ('PAP-036', 'Etiquetas adhesivas blancas', 'Paquete'),
                ('PAP-037', 'Corrector liquido', 'Pieza'),
                ('PAP-038', 'Cutter', 'Pieza'),
                ('PAP-039', 'Regla 30cm', 'Pieza'),
                ('PAP-040', 'Calculadora de escritorio', 'Pieza'),
                ('PAP-041', 'Toner para impresora', 'Pieza'),
                ('PAP-042', 'Cartucho de tinta negro', 'Pieza'),
                ('PAP-043', 'Cartucho de tinta color', 'Pieza'),
                ('PAP-044', 'Papel para plotter', 'Rollo'),
                ('PAP-045', 'Ligas de hule', 'Bolsa'),
                ('PAP-046', 'Tabla de apoyo con clip', 'Pieza'),
                ('PAP-047', 'Cinta de empaque', 'Pieza'),
                ('PAP-048', 'Marcadores para pizarron', 'Paquete'),
                ('PAP-049', 'Borrador para pizarron', 'Pieza'),
                ('PAP-050', 'Archivero de carton', 'Pieza'),
            ],

            # LIMPIEZA - 41 items
            Category.LIMPIEZA: [
                ('LIM-001', 'Jabon liquido para manos', 'Galon'),
                ('LIM-002', 'Gel antibacterial', 'Litro'),
                ('LIM-003', 'Papel higienico', 'Paquete'),
                ('LIM-004', 'Toallas interdobladas', 'Paquete'),
                ('LIM-005', 'Cloro', 'Galon'),
                ('LIM-006', 'Pino desinfectante', 'Galon'),
                ('LIM-007', 'Multiusos en spray', 'Pieza'),
                ('LIM-008', 'Limpiador de vidrios', 'Litro'),
                ('LIM-009', 'Desengrasante', 'Galon'),
                ('LIM-010', 'Detergente en polvo', 'Kilogramo'),
                ('LIM-011', 'Suavizante de telas', 'Litro'),
                ('LIM-012', 'Escoba', 'Pieza'),
                ('LIM-013', 'Trapeador', 'Pieza'),
                ('LIM-014', 'Recogedor', 'Pieza'),
                ('LIM-015', 'Cubeta plastica', 'Pieza'),
                ('LIM-016', 'Mop para pisos', 'Pieza'),
                ('LIM-017', 'Franela', 'Metro'),
                ('LIM-018', 'Fibra verde para tallar', 'Paquete'),
                ('LIM-019', 'Esponja doble uso', 'Paquete'),
                ('LIM-020', 'Guantes de latex limpieza', 'Par'),
                ('LIM-021', 'Bolsas de basura chica', 'Paquete'),
                ('LIM-022', 'Bolsas de basura mediana', 'Paquete'),
                ('LIM-023', 'Bolsas de basura grande', 'Paquete'),
                ('LIM-024', 'Bolsas de basura jumbo', 'Paquete'),
                ('LIM-025', 'Aromatizante en aerosol', 'Pieza'),
                ('LIM-026', 'Pastilla para sanitario', 'Paquete'),
                ('LIM-027', 'Destapacanos', 'Litro'),
                ('LIM-028', 'Sacudidor', 'Pieza'),
                ('LIM-029', 'Jalador de agua', 'Pieza'),
                ('LIM-030', 'Atomizador vacio', 'Pieza'),
                ('LIM-031', 'Cepillo para sanitario', 'Pieza'),
                ('LIM-032', 'Dispensador de jabon', 'Pieza'),
                ('LIM-033', 'Dispensador de papel', 'Pieza'),
                ('LIM-034', 'Bote de basura chico', 'Pieza'),
                ('LIM-035', 'Bote de basura grande', 'Pieza'),
                ('LIM-036', 'Insecticida', 'Pieza'),
                ('LIM-037', 'Removedor de sarro', 'Litro'),
                ('LIM-038', 'Cera para pisos', 'Galon'),
                ('LIM-039', 'Shampoo para alfombras', 'Litro'),
                ('LIM-040', 'Toallas humedas desinfectantes', 'Paquete'),
                ('LIM-041', 'Servicio de fumigacion', 'Servicio'),
            ],

            # MANTENIMIENTO MOTOS - 41 items
            Category.MANTENIMIENTO_MOTOS: [
                ('MOT-001', 'Aceite de motor 4T', 'Litro'),
                ('MOT-002', 'Aceite de motor 2T', 'Litro'),
                ('MOT-003', 'Filtro de aceite', 'Pieza'),
                ('MOT-004', 'Filtro de aire', 'Pieza'),
                ('MOT-005', 'Bujia', 'Pieza'),
                ('MOT-006', 'Cadena de transmision', 'Pieza'),
                ('MOT-007', 'Sprocket delantero', 'Pieza'),
                ('MOT-008', 'Sprocket trasero', 'Pieza'),
                ('MOT-009', 'Balatas delanteras', 'Juego'),
                ('MOT-010', 'Balatas traseras', 'Juego'),
                ('MOT-011', 'Llanta delantera', 'Pieza'),
                ('MOT-012', 'Llanta trasera', 'Pieza'),
                ('MOT-013', 'Camara delantera', 'Pieza'),
                ('MOT-014', 'Camara trasera', 'Pieza'),
                ('MOT-015', 'Bateria de moto', 'Pieza'),
                ('MOT-016', 'Cable de acelerador', 'Pieza'),
                ('MOT-017', 'Cable de clutch', 'Pieza'),
                ('MOT-018', 'Cable de freno', 'Pieza'),
                ('MOT-019', 'Cable de velocimetro', 'Pieza'),
                ('MOT-020', 'Foco delantero', 'Pieza'),
                ('MOT-021', 'Foco trasero', 'Pieza'),
                ('MOT-022', 'Direccional', 'Pieza'),
                ('MOT-023', 'Espejo retrovisor', 'Pieza'),
                ('MOT-024', 'Manija de clutch', 'Pieza'),
                ('MOT-025', 'Manija de freno', 'Pieza'),
                ('MOT-026', 'Pedal de freno', 'Pieza'),
                ('MOT-027', 'Palanca de cambios', 'Pieza'),
                ('MOT-028', 'Amortiguador trasero', 'Pieza'),
                ('MOT-029', 'Reten de aceite', 'Pieza'),
                ('MOT-030', 'Juntas de motor', 'Juego'),
                ('MOT-031', 'Clutch completo', 'Juego'),
                ('MOT-032', 'Kit de arrastre', 'Juego'),
                ('MOT-033', 'Puno de acelerador', 'Pieza'),
                ('MOT-034', 'Lubricante de cadena', 'Pieza'),
                ('MOT-035', 'Liquido de frenos', 'Litro'),
                ('MOT-036', 'Anticongelante', 'Litro'),
                ('MOT-037', 'Servicio de afinacion menor', 'Servicio'),
                ('MOT-038', 'Servicio de afinacion mayor', 'Servicio'),
                ('MOT-039', 'Servicio de frenos', 'Servicio'),
                ('MOT-040', 'Servicio electrico', 'Servicio'),
                ('MOT-041', 'Servicio de suspension', 'Servicio'),
            ],

            # MANTENIMIENTO AUTOMOVILES - 12 items
            Category.MANTENIMIENTO_AUTOMOVILES: [
                ('AUT-001', 'Aceite de motor sintetico', 'Litro'),
                ('AUT-002', 'Filtro de aceite automovil', 'Pieza'),
                ('AUT-003', 'Filtro de aire automovil', 'Pieza'),
                ('AUT-004', 'Filtro de gasolina', 'Pieza'),
                ('AUT-005', 'Balatas delanteras automovil', 'Juego'),
                ('AUT-006', 'Balatas traseras automovil', 'Juego'),
                ('AUT-007', 'Llantas automovil', 'Pieza'),
                ('AUT-008', 'Bateria de automovil', 'Pieza'),
                ('AUT-009', 'Servicio de afinacion menor auto', 'Servicio'),
                ('AUT-010', 'Servicio de afinacion mayor auto', 'Servicio'),
                ('AUT-011', 'Servicio de frenos auto', 'Servicio'),
                ('AUT-012', 'Verificacion vehicular', 'Servicio'),
            ],

            # MANTENIMIENTO BODEGAS - 12 items
            Category.MANTENIMIENTO_BODEGAS: [
                ('BOD-001', 'Pintura vinilica interior', 'Galon'),
                ('BOD-002', 'Pintura vinilica exterior', 'Galon'),
                ('BOD-003', 'Material electrico general', 'Lote'),
                ('BOD-004', 'Lamparas LED', 'Pieza'),
                ('BOD-005', 'Material de plomeria', 'Lote'),
                ('BOD-006', 'Cerraduras y chapas', 'Pieza'),
                ('BOD-007', 'Mantenimiento de portones', 'Servicio'),
                ('BOD-008', 'Servicio de impermeabilizacion', 'Servicio'),
                ('BOD-009', 'Servicio de electricista', 'Servicio'),
                ('BOD-010', 'Servicio de plomero', 'Servicio'),
                ('BOD-011', 'Servicio de aire acondicionado', 'Servicio'),
                ('BOD-012', 'Mantenimiento general instalaciones', 'Servicio'),
            ],

            # VIATICOS - 4 items
            Category.VIATICOS: [
                ('VIA-001', 'Hospedaje', 'Noche'),
                ('VIA-002', 'Alimentacion', 'Dia'),
                ('VIA-003', 'Transporte terrestre', 'Viaje'),
                ('VIA-004', 'Transporte aereo', 'Vuelo'),
            ],

            # SEGURIDAD E HIGIENE - 32 items
            Category.SEGURIDAD_HIGIENE: [
                ('SEG-001', 'Casco de seguridad para moto', 'Pieza'),
                ('SEG-002', 'Chaleco reflejante', 'Pieza'),
                ('SEG-003', 'Guantes de trabajo', 'Par'),
                ('SEG-004', 'Lentes de seguridad', 'Pieza'),
                ('SEG-005', 'Zapatos de seguridad', 'Par'),
                ('SEG-006', 'Botas de seguridad', 'Par'),
                ('SEG-007', 'Tapones auditivos', 'Par'),
                ('SEG-008', 'Faja de seguridad', 'Pieza'),
                ('SEG-009', 'Extintor polvo quimico 6kg', 'Pieza'),
                ('SEG-010', 'Extintor CO2', 'Pieza'),
                ('SEG-011', 'Recarga de extintor', 'Servicio'),
                ('SEG-012', 'Botiquin de primeros auxilios', 'Pieza'),
                ('SEG-013', 'Gasa esteril', 'Caja'),
                ('SEG-014', 'Vendas elasticas', 'Caja'),
                ('SEG-015', 'Alcohol', 'Litro'),
                ('SEG-016', 'Agua oxigenada', 'Litro'),
                ('SEG-017', 'Curitas adhesivas', 'Caja'),
                ('SEG-018', 'Guantes de latex desechables', 'Caja'),
                ('SEG-019', 'Cubrebocas', 'Caja'),
                ('SEG-020', 'Senalizacion de seguridad', 'Pieza'),
                ('SEG-021', 'Cinta de precaucion', 'Rollo'),
                ('SEG-022', 'Conos de seguridad', 'Pieza'),
                ('SEG-023', 'Lampara de emergencia', 'Pieza'),
                ('SEG-024', 'Impermeable', 'Pieza'),
                ('SEG-025', 'Careta de proteccion', 'Pieza'),
                ('SEG-026', 'Arnes de seguridad', 'Pieza'),
                ('SEG-027', 'Linea de vida', 'Pieza'),
                ('SEG-028', 'Detector de humo', 'Pieza'),
                ('SEG-029', 'Rodilleras de seguridad', 'Par'),
                ('SEG-030', 'Bloqueador solar', 'Pieza'),
                ('SEG-031', 'Capacitacion en seguridad', 'Servicio'),
                ('SEG-032', 'Estudio de proteccion civil', 'Servicio'),
            ],

            # PUBLICIDAD Y EVENTOS - 7 items
            Category.PUBLICIDAD_EVENTOS: [
                ('PUB-001', 'Impresion de lonas y banners', 'Pieza'),
                ('PUB-002', 'Volantes y flyers', 'Millar'),
                ('PUB-003', 'Tarjetas de presentacion', 'Millar'),
                ('PUB-004', 'Articulos promocionales', 'Lote'),
                ('PUB-005', 'Renta de espacio para eventos', 'Evento'),
                ('PUB-006', 'Servicio de diseno grafico', 'Servicio'),
                ('PUB-007', 'Publicidad en redes sociales', 'Campana'),
            ],

            # CONSUMIBLES - 8 items
            Category.CONSUMIBLES: [
                ('CON-001', 'Agua purificada garrafon', 'Pieza'),
                ('CON-002', 'Cafe', 'Kilogramo'),
                ('CON-003', 'Azucar', 'Kilogramo'),
                ('CON-004', 'Crema para cafe', 'Pieza'),
                ('CON-005', 'Vasos desechables', 'Paquete'),
                ('CON-006', 'Platos desechables', 'Paquete'),
                ('CON-007', 'Cucharas desechables', 'Paquete'),
                ('CON-008', 'Servilletas', 'Paquete'),
            ],

            # COMBUSTIBLES - 2 items
            Category.COMBUSTIBLES: [
                ('CMB-001', 'Gasolina magna', 'Litro'),
                ('CMB-002', 'Gasolina premium', 'Litro'),
            ],

            # NOMINA - 12 items
            Category.NOMINA: [
                ('NOM-001', 'Sueldos y salarios', 'Quincena'),
                ('NOM-002', 'Aguinaldo', 'Pago'),
                ('NOM-003', 'Vacaciones', 'Pago'),
                ('NOM-004', 'Prima vacacional', 'Pago'),
                ('NOM-005', 'PTU', 'Pago'),
                ('NOM-006', 'Bono de productividad', 'Pago'),
                ('NOM-007', 'Horas extras', 'Pago'),
                ('NOM-008', 'Comisiones', 'Pago'),
                ('NOM-009', 'Vales de despensa', 'Mes'),
                ('NOM-010', 'Seguro de vida', 'Mes'),
                ('NOM-011', 'Fondo de ahorro', 'Mes'),
                ('NOM-012', 'Uniformes', 'Lote'),
            ],

            # IMPUESTOS - 7 items
            Category.IMPUESTOS: [
                ('IMP-001', 'ISR retenido', 'Mes'),
                ('IMP-002', 'IVA por pagar', 'Mes'),
                ('IMP-003', 'IMSS patronal', 'Mes'),
                ('IMP-004', 'INFONAVIT', 'Bimestre'),
                ('IMP-005', 'Impuesto sobre nomina', 'Mes'),
                ('IMP-006', 'Tenencias vehiculares', 'Anual'),
                ('IMP-007', 'Derechos y licencias', 'Tramite'),
            ],
        }

        total_created = 0
        total_existing = 0

        for category_code, items_list in items_by_category.items():
            category = Category.objects.get(code=category_code)
            created_count = 0
            for code, name, unit in items_list:
                item, created = Item.objects.get_or_create(
                    code=code,
                    defaults={
                        'category': category,
                        'name': name,
                        'unit': unit,
                    }
                )
                if created:
                    created_count += 1
                    total_created += 1
                else:
                    total_existing += 1

            self.stdout.write(
                self.style.SUCCESS(f'  + {category.name}: {created_count} items creados')
                if created_count > 0
                else f'  - {category.name}: todos los items ya existen'
            )

        self.stdout.write(self.style.SUCCESS(
            f'\n  Total items creados: {total_created} | Ya existentes: {total_existing} | '
            f'Gran total: {total_created + total_existing}'
        ))
