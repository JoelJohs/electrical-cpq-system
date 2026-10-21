#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/var/www/mvp-project"
export PATH="/usr/local/bin:/root/.local/bin:$PATH"

echo "=========================================="
echo "=== Despliegue Continuo MVP en Ubuntu ===="
echo "=========================================="

if [[ ! -d "$APP_DIR" ]]; then
    echo "ERROR: Directorio de aplicación $APP_DIR no existe." >&2
    exit 1
fi

cd "$APP_DIR"

if [[ ! -f ".env" ]]; then
    echo "ERROR: Archivo $APP_DIR/.env no encontrado. Configúralo antes de desplegar." >&2
    exit 1
fi

UV_BIN=$(command -v uv || true)
if [[ -z "$UV_BIN" ]]; then
    echo "ERROR: 'uv' no encontrado en PATH ($PATH)." >&2
    exit 1
fi

echo "1. Obteniendo últimos cambios desde origin/main..."
git fetch origin main
git reset --hard origin/main

echo "2. Sincronizando dependencias herméticas con uv..."
"$UV_BIN" sync --frozen --no-dev

echo "3. Comprobando configuración de producción..."
"$UV_BIN" run python manage.py check --deploy

echo "4. Aplicando migraciones de base de datos..."
"$UV_BIN" run python manage.py migrate --noinput

echo "5. Recolectando archivos estáticos..."
"$UV_BIN" run python manage.py collectstatic --noinput

echo "6. Reiniciando servicio Gunicorn..."
sudo systemctl restart gunicorn

echo "7. Verificando estado del servicio..."
for _ in $(seq 1 10); do
    if sudo systemctl is-active --quiet gunicorn; then
        echo "Servicio Gunicorn activo y respondiendo."
        break
    fi
    sleep 1
done

if ! sudo systemctl is-active --quiet gunicorn; then
    echo "ERROR: El servicio Gunicorn falló al reiniciar." >&2
    sudo journalctl -u gunicorn -n 25 --no-pager
    exit 1
fi

echo "=== Despliegue finalizado con éxito ==="
