# AUTODIS - Sistema de Compras y Gestión de Presupuestos

Sistema integral para modernizar y optimizar el proceso de solicitud, aprobación y seguimiento de compras en AUTODIS.

## Características Principales

- **Centralización de Solicitudes**: Plataforma única accesible desde cualquier ubicación
- **Flujo de Aprobaciones Automatizado**: Notificaciones por correo electrónico
- **Control Presupuestal en Tiempo Real**: Por área, categoría y centro de costos
- **Reportes Analíticos**: Para toma de decisiones basada en datos
- **Historial Completo**: Trazabilidad total de todas las transacciones
- **Proyección de Presupuestos**: Basado en datos históricos

## Stack Tecnológico

- **Backend**: Django 4.2 + Django REST Framework
- **Base de Datos**: PostgreSQL
- **Caché y Tareas**: Redis + Celery
- **Frontend**: React (por implementar)
- **Servidor Web**: Gunicorn + Nginx (producción)

## Requisitos

- Python 3.10+
- PostgreSQL 13+
- Redis 6+ (para Celery)
- Node.js 18+ (para frontend)

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/princessofthedark/compras.git
cd compras
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y configurar:
- `SECRET_KEY`: Clave secreta de Django
- Credenciales de PostgreSQL (`DB_NAME`, `DB_USER`, `DB_PASSWORD`)
- Configuración de email SMTP
- URL de Redis

### 5. Crear base de datos PostgreSQL

```bash
createdb autodis_compras
```

O desde psql:
```sql
CREATE DATABASE autodis_compras;
CREATE USER autodis_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE autodis_compras TO autodis_user;
```

### 6. Aplicar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Poblar datos iniciales

```bash
python manage.py populate_initial_data
```

Este comando crea:
- 5 Áreas (Operaciones, Comercial, Administración, Finanzas, Personas y Comunicación)
- 4 Ubicaciones (Guadalajara, Culiacán, Puerto Vallarta, Oficinas Centrales)
- 12 Centros de Costos
- 12 Categorías de Presupuesto

### 8. Crear superusuario

```bash
python manage.py createsuperuser
```

### 9. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

El sistema estará disponible en `http://localhost:8000`

Panel de administración: `http://localhost:8000/admin`

## Estructura del Proyecto

```
compras/
├── autodis_compras/              # Proyecto principal
│   ├── settings/                 # Configuraciones
│   │   ├── base.py              # Configuración base
│   │   ├── development.py       # Desarrollo
│   │   └── production.py        # Producción
│   ├── apps/                     # Aplicaciones
│   │   ├── users/               # Usuarios, áreas, centros de costos
│   │   ├── budgets/             # Presupuestos, categorías, items
│   │   ├── requests/            # Solicitudes de compra
│   │   ├── reports/             # Reportes y análisis
│   │   └── notifications/       # Notificaciones por email
│   ├── urls.py                   # URLs principales
│   ├── wsgi.py                   # WSGI para producción
│   └── celery.py                 # Configuración Celery
├── manage.py                     # Comando de gestión Django
├── requirements.txt              # Dependencias Python
└── README.md                     # Este archivo
```

## Estructura Organizacional

### Áreas (5)
1. Operaciones
2. Comercial
3. Administración
4. Finanzas
5. Personas y Comunicación

### Centros de Costos (12)
1. OPERACIONES-GDL
2. OPERACIONES-CUL
3. OPERACIONES-PVR
4. COMERCIAL-VENTAS-NORTE
5. COMERCIAL-VENTAS-SUR
6. COMERCIAL-ECOMMERCE
7. ADMINISTRACION
8. FINANZAS
9. COMUNICACION
10. SISTEMAS
11. FISCAL-JURIDICO
12. DIRECCION-GENERAL

### Categorías de Presupuesto (12)
1. Papelería
2. Limpieza
3. Mantenimiento Motos
4. Mantenimiento Automóviles
5. Mantenimiento Bodegas
6. Viáticos
7. Seguridad e Higiene
8. Publicidad y Eventos
9. Consumibles
10. Combustibles
11. Nómina
12. Impuestos

## Roles y Permisos

### 1. Empleado
- Crear solicitudes para su área
- Ver todas las solicitudes de su área
- Editar solicitudes propias en estado "Pendiente aprobación gerente"
- Agregar comentarios

### 2. Gerente de Área
- Todo lo de Empleado +
- Aprobar solicitudes de su área
- Gestionar usuarios de su área
- Modo "Fuera de Oficina" para delegar aprobaciones
- Reportes de su área

### 3. Finanzas / Dirección General
- Vista completa de todas las áreas
- Aprobación final de todas las solicitudes
- Gestión de presupuestos
- Administración de categorías e items
- Gestión de usuarios de todas las áreas
- Cierre y reapertura de meses
- Reportes completos

## Flujo de Aprobaciones

1. **Empleado crea solicitud** → Estado: "Pendiente aprobación gerente"
2. **Notificación** → Gerente del área
3. **Gerente aprueba** → Estado: "Aprobada por gerente"
4. **Notificación** → Finanzas Y Dirección General
5. **Finanzas/Dir. General aprueba** → Estado: "Aprobada"
6. **Notificación** → Solicitante y Gerente

### Estados de Solicitud (10)
1. Borrador
2. Pendiente aprobación gerente
3. Aprobada por gerente
4. Aprobada
5. En proceso de compra
6. Comprada
7. Completada
8. Rechazada por gerente
9. Rechazada por Finanzas/Dir. General
10. Cancelada

## Control Presupuestal

El sistema controla presupuestos en tres niveles:
- Por Centro de Costos (12 centros)
- Por Categoría (12 categorías)
- Por Mes (solo solicitudes del mes en curso)

Cuando una solicitud excede el presupuesto disponible:
- Sistema muestra alerta visual
- Solicita justificación OBLIGATORIA
- PERMITE continuar (bloqueo suave)
- Aprobadores ven el exceso y justificación

## Gestión de Presupuestos

### Métodos de Carga

**1. Carga Manual**
- Pantalla de administración de presupuestos
- Ingreso manual por centro de costos y categoría

**2. Importación desde Excel**
- Subir archivo Excel con formato específico
- Carga automática de todos los presupuestos

**3. Copia de Mes Anterior**
- Copiar presupuestos del mes anterior
- Ajustar antes de confirmar

**4. Proyección de Año Nuevo**
- Calcular promedio del año anterior
- Sugerir presupuestos basados en datos reales

## Reportes Disponibles

1. **Gastos por Período**
   - Total gastado por mes, trimestre o año
   - Desglose por área, centro de costos y categoría

2. **Comparativo de Presupuesto**
   - Presupuestado vs Gastado
   - Identificación de variaciones

3. **Proyección para Año Siguiente**
   - Basado en gasto real histórico
   - Tendencias de crecimiento/decremento

4. **Gastos por Empleado**
   - Total solicitado por empleado
   - Patrones de gasto

5. **Proveedores Más Usados**
   - Frecuencia y montos por proveedor
   - Oportunidades de negociación

6. **Exportación**
   - Excel (.xlsx)
   - PDF

## Tareas con Celery

Para ejecutar tareas asíncronas (envío de emails, generación de reportes):

```bash
# En una terminal separada
celery -A autodis_compras worker -l info

# Para tareas programadas
celery -A autodis_compras beat -l info
```

## Pruebas

```bash
python manage.py test
```

## Despliegue en Producción

Ver archivo `DEPLOY.md` para instrucciones detalladas de despliegue.

## Contribuir

1. Fork el proyecto
2. Crear una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Propiedad de AUTODIS. Todos los derechos reservados.

## Soporte

Para soporte técnico, contactar a:
- Sistemas: sistemas@autodis.mx
- Finanzas: fernanda@autodis.mx

---

Desarrollado para AUTODIS - 2026
