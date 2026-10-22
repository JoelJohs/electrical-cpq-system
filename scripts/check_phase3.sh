#!/usr/bin/env bash
# Verificación automática de la Fase 3: Arquitectura Base y Datos (Catálogo Eléctrico).
# Uso:
#   ./scripts/check_phase3.sh
#
# Devuelve código de salida 0 solo si TODOS los ítems de la Fase 3 están en verde.

set -uo pipefail
cd "$(dirname "$0")/.."

PASS=0
FAIL=0
WARN=0

ok()   { printf '  \033[32m[PASS]\033[0m %s\n' "$1"; PASS=$((PASS + 1)); }
bad()  { printf '  \033[31m[FAIL]\033[0m %s\n' "$1"; FAIL=$((FAIL + 1)); }
warn() { printf '  \033[33m[WARN]\033[0m %s\n' "$1"; WARN=$((WARN + 1)); }

echo ""
echo "── Ítem 1: Modelado de Datos e Integridad en BD (Grafo Dirigido) ─"
if [ -f "src/catalog/models.py" ] && grep -q "prevent_self_relation" src/catalog/models.py && grep -q "unique_source_target_rel_type" src/catalog/models.py; then
  ok "Modelos Product y ProductCompatibility con CheckConstraint y UniqueConstraint"
else
  bad "Faltan modelos o restricciones de integridad en src/catalog/models.py"
fi

if [ -f "src/catalog/migrations/0001_initial.py" ]; then
  ok "Migración inicial de catálogo generada (0001_initial.py)"
else
  bad "Falta migración inicial en src/catalog/migrations/0001_initial.py"
fi

if [ -f "docker-compose.yml" ] && [ -x "scripts/db_dev.sh" ]; then
  ok "Contenedor PostgreSQL 17 desechable y script scripts/db_dev.sh configurados"
else
  bad "Falta docker-compose.yml o script scripts/db_dev.sh"
fi

echo ""
echo "── Ítem 2: Estructura Modular y Consultas O(1) sin N+1 ───────────"
if [ -f "src/catalog/selectors.py" ] && grep -q "get_product_compatibility_tree" src/catalog/selectors.py; then
  ok "Capa de selectores optimizada implementada en src/catalog/selectors.py"
else
  bad "Falta función get_product_compatibility_tree en src/catalog/selectors.py"
fi

if [ -f "src/catalog/schemas.py" ] && [ -f "src/catalog/enums.py" ]; then
  ok "Esquemas Pydantic v2 y enums de dominio definidos"
else
  bad "Faltan esquemas o enums en src/catalog/"
fi

echo ""
echo "── Ítem 3: API REST (Django Ninja) y Administración Django ───────"
if [ -f "src/catalog/api.py" ] && grep -q "catalog_router" src/catalog/api.py; then
  ok "Endpoints REST montados con Django Ninja en /api/"
else
  bad "Falta configuración de API Ninja en src/catalog/api.py"
fi

if [ -f "src/catalog/admin.py" ] && grep -q "ProductCompatibilityInline" src/catalog/admin.py; then
  ok "Django Admin configurado con inlines tabulares de compatibilidad"
else
  bad "Falta configuración de ProductAdmin o inlines en src/catalog/admin.py"
fi

echo ""
echo "── Ítem 4: Datos Semilla y Pruebas Automatizadas ─────────────────"
if uv run python manage.py test src.catalog.tests >/dev/null 2>&1; then
  ok "Suite completa de pruebas de catálogo y compatibilidades en verde"
else
  bad "Las pruebas de catálogo fallaron (ejecute: uv run python manage.py test src.catalog.tests)"
fi

if uv run ruff check . >/dev/null 2>&1 && uv run ruff format --check . >/dev/null 2>&1; then
  ok "Linters y formateo de código con Ruff en verde (0 errores)"
else
  bad "Existen errores de lint o formato (ejecute: uv run ruff check .)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
printf 'Resultado: %d PASS · %d FAIL · %d WARN\n' "$PASS" "$FAIL" "$WARN"
if [ "$FAIL" -eq 0 ]; then
  echo "Fase 3: EN OPERACIÓN ✅"
  echo "════════════════════════════════════════════════════════════════"
  exit 0
else
  echo "Fase 3: TIENE FALLOS ❌"
  echo "════════════════════════════════════════════════════════════════"
  exit 1
fi
