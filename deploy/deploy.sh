#!/usr/bin/env bash
set -e

APP_DIR="/var/www/mvp-project"

echo "=== Desplegando MVP ==="
cd "$APP_DIR"

echo "1. Obteniendo últimos cambios..."
git pull origin main

echo "2. Sincronizando dependencias con uv..."
uv sync --frozen --no-dev

echo "3. Ejecutando migraciones..."
uv run python manage.py migrate --noinput

echo "4. Recolectando archivos estáticos..."
uv run python manage.py collectstatic --noinput

echo "5. Reiniciando servicio Gunicorn..."
sudo systemctl restart gunicorn

echo "=== Despliegue finalizado con éxito ==="
