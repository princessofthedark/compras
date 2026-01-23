#!/bin/bash
# Script de instalación automática para Digital Ocean Droplet
# Ubuntu 22.04 LTS

set -e

echo "======================================"
echo "AUTODIS - Sistema de Compras"
echo "Instalación en Digital Ocean Droplet"
echo "======================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables - PERSONALIZAR ANTES DE EJECUTAR
DOMAIN="compras.autodis.mx"
EMAIL="sistemas@autodis.mx"
DB_NAME="autodis_compras"
DB_USER="autodis_user"
DB_PASSWORD="CAMBIAR_PASSWORD_SEGURO"
APP_USER="autodis"

echo -e "${GREEN}[1/10] Actualizando sistema...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}[2/10] Instalando dependencias...${NC}"
apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib \
    redis-server nginx supervisor git curl ufw certbot python3-certbot-nginx

echo -e "${GREEN}[3/10] Configurando firewall...${NC}"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo -e "${GREEN}[4/10] Configurando PostgreSQL...${NC}"
sudo -u postgres psql <<EOF
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE ${DB_USER} SET client_encoding TO 'utf8';
ALTER ROLE ${DB_USER} SET default_transaction_isolation TO 'read committed';
ALTER ROLE ${DB_USER} SET timezone TO 'America/Mexico_City';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\q
EOF

echo -e "${GREEN}[5/10] Configurando Redis...${NC}"
systemctl enable redis-server
systemctl start redis-server

echo -e "${GREEN}[6/10] Creando usuario de aplicación...${NC}"
useradd -m -s /bin/bash ${APP_USER} || echo "Usuario ya existe"

echo -e "${GREEN}[7/10] Clonando repositorio...${NC}"
sudo -u ${APP_USER} bash <<EOF
cd /home/${APP_USER}
git clone https://github.com/princessofthedark/compras.git
cd compras
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
EOF

echo -e "${GREEN}[8/10] Configurando variables de entorno...${NC}"
cat > /home/${APP_USER}/compras/.env <<EOF
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=${DOMAIN},www.${DOMAIN}

DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=compras@autodis.mx
EMAIL_HOST_PASSWORD=CONFIGURAR_PASSWORD
DEFAULT_FROM_EMAIL=compras@autodis.mx
EOF

chown ${APP_USER}:${APP_USER} /home/${APP_USER}/compras/.env

echo -e "${GREEN}[9/10] Ejecutando migraciones y recolectando archivos estáticos...${NC}"
sudo -u ${APP_USER} bash <<EOF
cd /home/${APP_USER}/compras
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py populate_initial_data
EOF

echo -e "${GREEN}[10/10] Configurando servicios...${NC}"

# Gunicorn systemd service
cat > /etc/systemd/system/gunicorn.service <<EOF
[Unit]
Description=Gunicorn daemon for AUTODIS Compras
After=network.target

[Service]
User=${APP_USER}
Group=www-data
WorkingDirectory=/home/${APP_USER}/compras
Environment="PATH=/home/${APP_USER}/compras/venv/bin"
EnvironmentFile=/home/${APP_USER}/compras/.env
ExecStart=/home/${APP_USER}/compras/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/${APP_USER}/compras/gunicorn.sock \
          --timeout 120 \
          autodis_compras.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Celery worker supervisor config
cat > /etc/supervisor/conf.d/celery.conf <<EOF
[program:celery-worker]
command=/home/${APP_USER}/compras/venv/bin/celery -A autodis_compras worker -l info --concurrency=2
directory=/home/${APP_USER}/compras
user=${APP_USER}
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log
environment=PATH="/home/${APP_USER}/compras/venv/bin"

[program:celery-beat]
command=/home/${APP_USER}/compras/venv/bin/celery -A autodis_compras beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/home/${APP_USER}/compras
user=${APP_USER}
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
environment=PATH="/home/${APP_USER}/compras/venv/bin"
EOF

mkdir -p /var/log/celery
chown ${APP_USER}:${APP_USER} /var/log/celery

# Nginx configuration
cat > /etc/nginx/sites-available/${DOMAIN} <<EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /home/${APP_USER}/compras/staticfiles/;
    }

    location /media/ {
        alias /home/${APP_USER}/compras/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/${APP_USER}/compras/gunicorn.sock;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
        proxy_redirect off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Start services
systemctl start gunicorn
systemctl enable gunicorn

supervisorctl reread
supervisorctl update

systemctl restart nginx

echo -e "${GREEN}======================================"
echo -e "Instalación completada!"
echo -e "======================================${NC}"
echo -e "${YELLOW}Próximos pasos:${NC}"
echo -e "1. Configurar DNS para apuntar ${DOMAIN} a esta IP"
echo -e "2. Ejecutar: certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
echo -e "3. Crear superusuario: sudo -u ${APP_USER} bash -c 'cd /home/${APP_USER}/compras && source venv/bin/activate && python manage.py createsuperuser'"
echo -e "4. Configurar EMAIL_HOST_PASSWORD en /home/${APP_USER}/compras/.env"
echo -e ""
echo -e "${GREEN}URL de acceso: http://${DOMAIN}/admin${NC}"
