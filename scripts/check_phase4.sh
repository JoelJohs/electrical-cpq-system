#!/usr/bin/env bash
# Verificación automática de la Fase 4: Desarrollo del Core (Happy Path - CPQ Técnico).
# Uso:
#   ./scripts/check_phase4.sh
#
# Devuelve código de salida 0 solo si TODOS los ítems de la Fase 4 están en verde.

set -uo pipefail
cd "$(dirname "$0")/.."

PASS=0
FAIL=0
WARN=0

ok()   { printf '  \033[32m[PASS]\033[0m %s\n' "$1"; PASS=$((PASS + 1)); }
bad()  { printf '  \033[31m[FAIL]\033[0m %s\n' "$1"; FAIL=$((FAIL + 1)); }
warn() { printf '  \033[33m[WARN]\033[0m %s\n' "$1"; WARN=$((WARN + 1)); }

echo ""
echo "── Bloque 1: Modelo de Cotizaciones Técnicas y Persistencia ────────"
if [ -f "src/quotes/models.py" ] && grep -q "class Quote(" src/quotes/models.py && grep -q "class QuoteItem(" src/quotes/models.py; then
  ok "Modelos Quote y QuoteItem implementados con integridad referencial"
else
  bad "Faltan modelos Quote o QuoteItem en src/quotes/models.py"
fi

if [ -f "src/quotes/enums.py" ] && grep -q "class QuoteStatus" src/quotes/enums.py; then
  ok "Enum QuoteStatus con estados formales (DRAFT, VALIDATED, SENT, ACCEPTED, CANCELLED)"
else
  bad "Falta enum QuoteStatus en src/quotes/enums.py"
fi

if [ -f "src/quotes/migrations/0001_initial.py" ]; then
  ok "Migraciones de quotes generadas y aplicadas"
else
  bad "Falta migración inicial en src/quotes/migrations/"
fi

echo ""
echo "── Bloque 2: Motor de Reglas Técnicas y Validación Electromecánica ─"
if [ -f "src/quotes/rules.py" ] && grep -q "validate_quote_configuration" src/quotes/rules.py; then
  ok "Motor algorítmico de validación (espacios, amperajes y REQUIRES antilazos)"
else
  bad "Falta función validate_quote_configuration en src/quotes/rules.py"
fi

if [ -f "src/quotes/selectors.py" ] && grep -q "get_quote_bom" src/quotes/selectors.py; then
  ok "Generador y agregador de Lista de Materiales (BOM) en src/quotes/selectors.py"
else
  bad "Falta función get_quote_bom en src/quotes/selectors.py"
fi

echo ""
echo "── Bloque 3: API REST del Configurador (Django Ninja) ──────────────"
if [ -f "src/quotes/schemas.py" ] && grep -q "QuoteDetailSchema" src/quotes/schemas.py && grep -q "BOMResponseSchema" src/quotes/schemas.py; then
  ok "Esquemas Pydantic v2 tipados en src/quotes/schemas.py"
else
  bad "Faltan esquemas tipados en src/quotes/schemas.py"
fi

if [ -f "src/quotes/api.py" ] && grep -q "quotes_router" src/quotes/api.py; then
  ok "Router REST de cotizaciones montado en /api/v1/quotes/"
else
  bad "Falta configuración de router Ninja en src/quotes/api.py"
fi

echo ""
echo "── Bloques 4 y 5: Interfaces Web (Ventas e Integradores) ───────────"
if [ -f "src/quotes/templates/quotes/base_quotes.html" ] && [ -f "src/quotes/templates/quotes/quick_quote.html" ] && [ -f "src/quotes/templates/quotes/configurator.html" ] && [ -f "src/quotes/templates/quotes/bom_detail.html" ]; then
  ok "Plantillas web completas (Layout ABV, Vista rápida, Configurador 2D y Resumen BOM)"
else
  bad "Faltan plantillas web en src/quotes/templates/quotes/"
fi

if [ -f "src/quotes/views.py" ] && [ -f "src/quotes/urls.py" ]; then
  ok "Controladores de vista y rutas web registradas en /quotes/"
else
  bad "Faltan controladores o rutas web en src/quotes/"
fi

echo ""
echo "── Bloque 6: Panel de Administración y Pruebas Automatizadas ───────"
if [ -f "src/quotes/admin.py" ] && grep -q "QuoteAdmin" src/quotes/admin.py && grep -q "QuoteItemInline" src/quotes/admin.py; then
  ok "Django Admin configurado con QuoteAdmin e inlines QuoteItemInline"
else
  bad "Falta configuración de QuoteAdmin en src/quotes/admin.py"
fi

if uv run python manage.py test quotes >/dev/null 2>&1; then
  ok "Suite completa de pruebas de cotizaciones (modelos, servicios, reglas, bom, api, vistas) en verde"
else
  bad "Las pruebas de quotes fallaron (ejecute: uv run python manage.py test quotes)"
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
  echo "Fase 4: EN OPERACIÓN ✅ (Happy Path Completo)"
  echo "════════════════════════════════════════════════════════════════"
  exit 0
else
  echo "Fase 4: TIENE FALLOS ❌"
  echo "════════════════════════════════════════════════════════════════"
  exit 1
fi
