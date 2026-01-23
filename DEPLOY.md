# Guía de Despliegue - AUTODIS Sistema de Compras

## Opción 1: Digital Ocean App Platform (Recomendado - Más Fácil)

Digital Ocean App Platform es un servicio PaaS que maneja automáticamente el escalado, SSL y actualizaciones.

### Prerrequisitos

1. Cuenta en Digital Ocean: https://digitalocean.com
2. GitHub conectado a Digital Ocean
3. Código pusheado a GitHub

### Paso 1: Crear Base de Datos PostgreSQL

1. En Digital Ocean, ir a **Databases** → **Create Database**
2. Seleccionar:
   - Engine: **PostgreSQL 15**
   - Plan: **Basic** (para empezar)
   - Datacenter: **New York** (o el más cercano)
   - Database name: `autodis_compras`
3. Crear y esperar ~5 minutos
4. Guardar las credenciales de conexión

### Paso 2: Crear Redis Cluster

1. En Digital Ocean, ir a **Databases** → **Create Database**
2. Seleccionar:
   - Engine: **Redis 7**
   - Plan: **Basic**
   - Datacenter: Mismo que PostgreSQL
3. Crear y guardar credenciales

### Paso 3: Crear App en App Platform

1. Ir a **Apps** → **Create App**
2. Conectar con GitHub y seleccionar repositorio `compras`
3. Seleccionar branch: `claude/read-pdf-build-yznqI` (o main después de merge)
4. Digital Ocean detectará automáticamente que es Python/Django

### Paso 4: Configurar Componentes de la App

Digital Ocean creará 3 componentes automáticamente:

#### Web Service (Django)
```yaml
name: web
source:
  repo: princessofthedark/compras
  branch: claude/read-pdf-build-yznqI
build_command: |
  pip install -r requirements.txt
  python manage.py collectstatic --noinput
  python manage.py migrate
run_command: gunicorn autodis_compras.wsgi:application --bind 0.0.0.0:8000
environment_slug: python
instance_count: 1
instance_size_slug: basic-xxs
```

#### Worker (Celery)
```yaml
name: worker
source:
  repo: princessofthedark/compras
  branch: claude/read-pdf-build-yznqI
build_command: pip install -r requirements.txt
run_command: celery -A autodis_compras worker -l info
environment_slug: python
instance_count: 1
instance_size_slug: basic-xxs
```

#### Beat (Celery Scheduler)
```yaml
name: beat
source:
  repo: princessofthedark/compras
  branch: claude/read-pdf-build-yznqI
build_command: pip install -r requirements.txt
run_command: celery -A autodis_compras beat -l info
environment_slug: python
instance_count: 1
instance_size_slug: basic-xxs
```

### Paso 5: Configurar Variables de Entorno

En la sección **Environment Variables**, agregar:

```bash
# Django
SECRET_KEY=<generar-clave-segura-aqui>
DEBUG=False
ALLOWED_HOSTS=${APP_DOMAIN},compras.autodis.mx
DJANGO_SETTINGS_MODULE=autodis_compras.settings.production

# Database (copiar de Digital Ocean Database)
DB_NAME=autodis_compras
DB_USER=<usuario-postgres>
DB_PASSWORD=<password-postgres>
DB_HOST=<host-postgres>
DB_PORT=25060

# Redis (copiar de Digital Ocean Redis)
REDIS_URL=rediss://<usuario>:<password>@<host>:25061

# Email (configurar con tu proveedor SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=compras@autodis.mx
EMAIL_HOST_PASSWORD=<password-email>
DEFAULT_FROM_EMAIL=compras@autodis.mx
```

**Generar SECRET_KEY segura:**
```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Paso 6: Configurar Dominio Personalizado (Opcional)

1. En App Settings → Domains
2. Agregar: `compras.autodis.mx`
3. Configurar DNS en tu proveedor:
   ```
   Type: CNAME
   Name: compras
   Value: <tu-app>.ondigitalocean.app
   ```
4. Digital Ocean manejará SSL automáticamente

### Paso 7: Deploy

1. Click en **Create Resources**
2. Esperar ~10 minutos para el primer despliegue
3. Digital Ocean ejecutará migraciones automáticamente

### Paso 8: Crear Superusuario

Conectar por consola a la app:

```bash
# Desde tu computadora local con doctl CLI instalado
doctl apps create-deployment <app-id>

# O usar la consola web
# Apps → Tu App → Console → Seleccionar "web"
python manage.py createsuperuser
python manage.py populate_initial_data
```

### Paso 9: Configurar Almacenamiento para Archivos (Media)

Para archivos adjuntos, usar **Spaces** (S3-compatible):

1. Crear un Space en Digital Ocean
2. Instalar dependencias:
   ```bash
   pip install boto3 django-storages
   ```
3. Configurar en `settings/production.py`:
   ```python
   # Ver archivo app.yaml para configuración completa
   ```

---

## Opción 2: Digital Ocean Droplet (Más Control)

Si necesitas más control o costos más bajos, usar un Droplet (VPS).

### Prerrequisitos

- Droplet Ubuntu 22.04 LTS
- Dominio apuntando al Droplet
- Conocimientos básicos de Linux

### Instalación Rápida

```bash
# 1. Conectar al droplet
ssh root@tu-servidor

# 2. Ejecutar script de instalación
curl -O https://raw.githubusercontent.com/princessofthedark/compras/main/scripts/deploy_droplet.sh
chmod +x deploy_droplet.sh
./deploy_droplet.sh
```

El script instalará:
- Nginx
- PostgreSQL
- Redis
- Gunicorn
- Supervisor (para Celery)
- Certbot (SSL)

---

## Opción 3: Vercel (Solo para Frontend)

**IMPORTANTE**: Vercel NO es apropiado para el backend Django. Úsalo SOLO para el frontend React.

### Arquitectura Recomendada

```
Frontend (Vercel)              Backend (Digital Ocean)
┌─────────────────┐           ┌──────────────────────┐
│  React App      │  ←────→   │  Django API          │
│  Next.js        │   HTTPS   │  + PostgreSQL        │
│                 │           │  + Redis/Celery      │
└─────────────────┘           └──────────────────────┘
```

### Configuración

1. **Backend**: Desplegar en Digital Ocean (Opción 1 o 2)
2. **Frontend**: Crear app Next.js/React
3. **Vercel**:
   ```bash
   cd frontend
   vercel deploy --prod
   ```
4. **Conectar**: Frontend llama a API en `https://compras.autodis.mx/api`

---

## Costos Estimados (Digital Ocean App Platform)

### Configuración Inicial (Pequeña)
- **Web Service** (Basic XXS): $5/mes
- **Worker** (Basic XXS): $5/mes
- **Beat** (Basic XXS): $5/mes
- **PostgreSQL** (Basic 1GB): $15/mes
- **Redis** (Basic 1GB): $15/mes

**Total**: ~$45/mes

### Configuración Producción (Mediana)
- **Web Service** (Basic M): $25/mes
- **Worker** (Basic S): $12/mes
- **Beat** (Basic XXS): $5/mes
- **PostgreSQL** (Basic 2GB): $30/mes
- **Redis** (Basic 2GB): $30/mes
- **Spaces** (250GB): $5/mes

**Total**: ~$107/mes

### Alternativa con Droplet (Más Económico)
- **Droplet** (4GB RAM): $24/mes
- Todo incluido (PostgreSQL, Redis, Nginx)

**Total**: $24/mes (pero requiere más mantenimiento)

---

## Recomendación Final

### Para Empezar (MVP/Pruebas)
✅ **Digital Ocean App Platform** - Fácil, rápido, sin configuración

### Para Producción (Empresarial)
✅ **Digital Ocean Droplet** o **App Platform** según presupuesto

### Frontend Separado
✅ **Vercel** para React + **Digital Ocean** para Django API

---

## Siguiente Paso

¿Qué opción prefieres?
1. **App Platform** → Te creo el archivo `app.yaml` para despliegue automático
2. **Droplet** → Te creo el script completo de instalación
3. **Híbrido** (Vercel + DO) → Te creo la configuración para ambos

Dime cuál prefieres y continúo con la configuración específica.
