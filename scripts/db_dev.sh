#!/usr/bin/env bash
# ==============================================================================
# Script de control para la base de datos PostgreSQL local en Docker
# Uso:
#   ./scripts/db_dev.sh up       # Iniciar base de datos
#   ./scripts/db_dev.sh down     # Detener contenedor
#   ./scripts/db_dev.sh reset    # Resetear completamente datos (destructivo / limpio)
#   ./scripts/db_dev.sh status   # Ver estado del contenedor y healthcheck
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

ACTION="${1:-status}"

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "AVISO: Docker no se encuentra instalado en este sistema."
        echo "Si no utilizas Docker localmente, puedes operar con SQLite configurado por defecto en .env"
        return 1
    fi
    return 0
}

case "$ACTION" in
    up)
        if check_docker; then
            echo "Iniciando PostgreSQL 17 en Docker..."
            docker compose up -d db
            echo "Esperando que PostgreSQL esté listo..."
            docker compose exec db sh -c 'until pg_isready -U postgres -d electrical_cpq; do sleep 1; done'
            echo "Base de datos lista en localhost:5432 (electrical_cpq)."
        fi
        ;;
    down)
        if check_docker; then
            echo "Deteniendo contenedor de base de datos..."
            docker compose down
        fi
        ;;
    reset)
        if check_docker; then
            echo "ADVERTENCIA: Se eliminará el volumen local de PostgreSQL y se reiniciará vacío."
            docker compose down -v
            docker compose up -d db
            echo "Esperando arranque..."
            docker compose exec db sh -c 'until pg_isready -U postgres -d electrical_cpq; do sleep 1; done'
            echo "Aplicando migraciones limpias..."
            uv run python manage.py migrate
            echo "Base de datos reseteada y migrada con éxito."
        fi
        ;;
    status)
        if check_docker; then
            docker compose ps
        fi
        ;;
    *)
        echo "Uso: $0 {up|down|reset|status}" >&2
        exit 1
        ;;
esac
