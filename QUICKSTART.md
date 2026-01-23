# Inicio Rápido - Despliegue en Digital Ocean

## Método 1: App Platform (Recomendado para empezar)

### Paso a Paso en 10 Minutos

**1. Crear cuenta en Digital Ocean**
- Ir a https://digitalocean.com
- Registrarse (tarjeta requerida, pero $200 crédito gratis por 60 días)

**2. Crear Redis Database**
```
Digital Ocean Dashboard → Databases → Create
- Engine: Redis 7
- Plan: Basic ($15/mes)
- Region: New York 3
- Click: Create Database Cluster
```
⏰ Esperar 3-5 minutos

**3. Copiar URL de Redis**
```
En la página del Redis creado, copiar:
"Public network" → Connection string
Ejemplo: rediss://default:XXXX@db-redis-nyc3-12345.ondigitalocean.com:25061
```

**4. Crear App desde GitHub**
```
Apps → Create App
- Source: GitHub
- Repository: princessofthedark/compras
- Branch: claude/read-pdf-build-yznqI
- Autodeploy: ✓ (check)
```

**5. Digital Ocean detecta automáticamente:**
- ✓ Python/Django
- ✓ Crea base de datos PostgreSQL
- ✓ Lee .do/app.yaml

**6. Configurar Variables de Entorno SECRETAS**

En la sección de Environment Variables, agregar:

```bash
# SECRET_KEY - Generar con este comando en tu terminal local:
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# REDIS_URL - Copiar del paso 3
rediss://default:PASSWORD@HOST:25061

# EMAIL (Gmail como ejemplo)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=compras@autodis.mx
EMAIL_HOST_PASSWORD=tu-app-password-de-gmail
```

**Para Gmail App Password:**
1. Ir a https://myaccount.google.com/security
2. Activar "2-Step Verification"
3. Ir a "App passwords"
4. Generar password para "Mail"
5. Copiar el password de 16 dígitos

**7. Deploy!**
```
Click: Create Resources
```
⏰ Esperar 10-15 minutos

**8. Crear Usuario Administrador**

Una vez desplegado:
```
Apps → Tu App → Console (tab superior)
Seleccionar componente: web
Ejecutar:
  python manage.py createsuperuser

Ingresar:
  Email: fernanda@autodis.mx
  Username: fernanda
  Password: (tu password seguro)
```

**9. Poblar Datos Iniciales**
```bash
python manage.py populate_initial_data
```

**10. ¡Listo!**
```
URL: https://tu-app-random.ondigitalocean.app/admin
Login con usuario creado
```

---

## Método 2: Droplet (Más económico)

### Instalación Automatizada

**1. Crear Droplet**
```
Digital Ocean → Droplets → Create
- Image: Ubuntu 22.04 LTS
- Size: Basic $24/mes (4GB RAM)
- Region: New York 3
- Authentication: SSH Key
- Hostname: autodis-compras
```

**2. Conectar por SSH**
```bash
ssh root@TU_IP_DEL_DROPLET
```

**3. Descargar y ejecutar script**
```bash
curl -o setup.sh https://raw.githubusercontent.com/princessofthedark/compras/claude/read-pdf-build-yznqI/scripts/setup_digitalocean.sh

# IMPORTANTE: Editar el script primero
nano setup.sh
# Cambiar:
#   - DOMAIN="compras.autodis.mx"
#   - EMAIL="sistemas@autodis.mx"
#   - DB_PASSWORD="PASSWORD_SEGURO_AQUI"

# Ejecutar
chmod +x setup.sh
./setup.sh
```

**4. Configurar DNS**
```
En tu proveedor de dominios (GoDaddy, Namecheap, etc.):

Type: A
Name: compras
Value: TU_IP_DEL_DROPLET
TTL: 3600
```

**5. Instalar SSL (después de configurar DNS)**
```bash
certbot --nginx -d compras.autodis.mx
```

**6. Crear Superusuario**
```bash
sudo -u autodis bash -c 'cd /home/autodis/compras && source venv/bin/activate && python manage.py createsuperuser'
```

**7. Listo!**
```
URL: https://compras.autodis.mx/admin
```

---

## Comparación de Costos

| Característica | App Platform | Droplet |
|---------------|--------------|---------|
| **Costo mensual** | ~$45/mes | ~$24/mes |
| **Configuración** | 10 minutos | 20 minutos |
| **Mantenimiento** | Automático | Manual |
| **Escalabilidad** | Automática | Manual |
| **Backups** | Automáticos | Configurar |
| **SSL** | Automático | Certbot |
| **Recomendado para** | Empezar rápido | Reducir costos |

---

## Solución de Problemas Comunes

### Error: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Error: "ALLOWED_HOSTS"
Agregar dominio a variable de entorno:
```bash
ALLOWED_HOSTS=${APP_DOMAIN},.ondigitalocean.app,compras.autodis.mx
```

### Error: "static files not found"
```bash
python manage.py collectstatic --noinput
```

### Celery no envía emails
Verificar en consola:
```bash
# Ver logs de worker
supervisorctl tail -f celery-worker

# O en App Platform
Apps → worker → Runtime Logs
```

---

## Monitoreo

### App Platform
```
Apps → Tu App → Insights
- Ver CPU, RAM, requests
- Ver logs en tiempo real
```

### Droplet
```bash
# Ver logs de Django
sudo tail -f /var/log/nginx/access.log

# Ver logs de Celery
sudo tail -f /var/log/celery/worker.log

# Estado de servicios
systemctl status gunicorn
systemctl status nginx
supervisorctl status
```

---

## Actualizaciones

### App Platform (Automático)
```
Cada git push a la rama configurada despliega automáticamente
```

### Droplet (Manual)
```bash
sudo -u autodis bash -c '
  cd /home/autodis/compras
  git pull origin main
  source venv/bin/activate
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py collectstatic --noinput
'

sudo systemctl restart gunicorn
sudo supervisorctl restart all
```

---

## Siguiente Paso

¿Cuál método prefieres?
- **App Platform**: Más fácil, continúa con los pasos arriba
- **Droplet**: Más económico, ejecuta el script
- **Ayuda**: Dime en qué paso necesitas ayuda

¡Éxito con el deployment! 🚀
