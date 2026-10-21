#!/usr/bin/env bash
# ==============================================================================
# Script de aprovisionamiento base para VPS con Ubuntu 24.04 LTS (Noble Numbat)
# Uso:
#   sudo ./deploy/provision_ubuntu2404.sh
# ==============================================================================
set -euo pipefail

echo "=== Iniciando aprovisionamiento en Ubuntu 24.04 LTS ==="

if [[ "$EUID" -ne 0 ]]; then
    echo "ERROR: Este script debe ejecutarse con privilegios de superusuario (sudo)." >&2
    exit 1
fi

APP_DIR="/var/www/mvp-project"
DEPLOY_USER="${SUDO_USER:-$(whoami)}"

echo "1. Actualizando índices de paquetes y sistema base..."
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

echo "2. Instalando herramientas esenciales del sistema y Nginx..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    git \
    build-essential \
    pkg-config \
    libpq-dev \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw

echo "3. Instalando manejador de paquetes hermético 'uv'..."
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
else
    echo "'uv' ya se encuentra instalado en $(command -v uv)."
fi

# Asegurar que uv esté disponible globalmente en /usr/local/bin
if [[ -f "/root/.local/bin/uv" && ! -f "/usr/local/bin/uv" ]]; then
    cp "/root/.local/bin/uv" "/usr/local/bin/uv"
    chmod +x "/usr/local/bin/uv"
fi

echo "4. Creando estructura de directorios en $APP_DIR..."
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/staticfiles"
mkdir -p "$APP_DIR/media"
mkdir -p /var/log/gunicorn

# Permisos: el usuario de despliegue es el propietario, www-data pertenece al grupo
chown -R "$DEPLOY_USER:www-data" "$APP_DIR"
chmod -R 775 "$APP_DIR"

echo "5. Configurando firewall básico (UFW)..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "6. Habilitando servicio Nginx..."
systemctl enable --now nginx

echo "=== Aprovisionamiento base completado con éxito ==="
echo "Siguientes pasos:"
echo "1. Clonar el repositorio en $APP_DIR si aún no está clonado."
echo "2. Crear el archivo $APP_DIR/.env con la configuración de producción."
echo "3. Copiar deploy/gunicorn.service a /etc/systemd/system/ y habilitarlo."
echo "4. Copiar deploy/nginx.conf a /etc/nginx/sites-available/ y habilitarlo."
echo "5. Ejecutar deploy/setup_ssl.sh <tu-dominio.com> <tu-email> para HTTPS."
