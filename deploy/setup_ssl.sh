#!/usr/bin/env bash
# ==============================================================================
# Script de emisión y renovación automática de certificados SSL/TLS con Certbot
# Uso:
#   sudo ./deploy/setup_ssl.sh <dominio> <email>
# Ejemplo:
#   sudo ./deploy/setup_ssl.sh app.mi-dominio.com admin@mi-dominio.com
# ==============================================================================
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
    echo "ERROR: Este script debe ejecutarse con privilegios de superusuario (sudo)." >&2
    exit 1
fi

DOMAIN="${1:-}"
EMAIL="${2:-}"

if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
    echo "Uso: sudo $0 <dominio> <email>" >&2
    echo "Ejemplo: sudo $0 api.ejemplo.com admin@ejemplo.com" >&2
    exit 1
fi

echo "=== Configurando SSL/TLS para $DOMAIN ==="

if ! command -v certbot >/dev/null 2>&1; then
    echo "Instalando certbot y plugin de nginx..."
    apt-get update -y
    apt-get install -y certbot python3-certbot-nginx
fi

NGINX_SITE="/etc/nginx/sites-available/mvp-project"
if [[ -f "$NGINX_SITE" ]]; then
    echo "Actualizando server_name en $NGINX_SITE..."
    sed -i "s/server_name .*/server_name $DOMAIN;/g" "$NGINX_SITE"
    nginx -t
    systemctl reload nginx
fi

echo "Solicitando certificado SSL a Let's Encrypt para $DOMAIN..."
certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    -m "$EMAIL" \
    --redirect

echo "Verificando el temporizador de auto-renovación de systemd..."
systemctl enable --now certbot.timer
systemctl status certbot.timer --no-pager

echo "=== Certificado SSL instalado y redirección HTTPS activa para $DOMAIN ==="
