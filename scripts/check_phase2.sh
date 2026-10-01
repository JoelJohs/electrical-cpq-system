#!/usr/bin/env bash
# Verificación automática de la Fase 2: Configuración Inicial y Repositorio.
# Uso:
#   ./scripts/check_phase2.sh                # modo remoto (exige CI + despliegue)
#   ./scripts/check_phase2.sh --local        # modo local: CI/despliegue quedan como
#                                            # PENDIENTE en vez de FAIL, y se prueba
#                                            # el Hello World contra un servidor local
#   ./scripts/check_phase2.sh --remote OWNER/REPO   # añade verificación de branch protection
#
# Devuelve código de salida 0 solo si TODOS los ítems del modo elegido están en operación.

set -uo pipefail
cd "$(dirname "$0")/.."

MODE="remote"
REMOTE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --local)  MODE="local"; shift ;;
    --remote) REMOTE="${2:-}"; shift 2 ;;
    *) echo "Argumento desconocido: $1" >&2; exit 2 ;;
  esac
done

PASS=0
FAIL=0
WARN=0
PEND=0

ok()   { printf '  \033[32m[PASS]\033[0m %s\n' "$1"; PASS=$((PASS + 1)); }
bad()  { printf '  \033[31m[FAIL]\033[0m %s\n' "$1"; FAIL=$((FAIL + 1)); }
warn() { printf '  \033[33m[WARN]\033[0m %s\n' "$1"; WARN=$((WARN + 1)); }
pend() { printf '  \033[36m[PEND]\033[0m %s\n' "$1"; PEND=$((PEND + 1)); }

# En modo local, lo que depende de infraestructura remota se pospone (PEND)
# en lugar de fallar. En modo remoto es un FAIL real.
infra() {
  if [[ "$MODE" == "local" ]]; then pend "$1"; else bad "$1"; fi
}

echo ""
echo "── Ítem 1: Repositorio Git con ramas protegidas ──────────────────"
if git rev-parse --git-dir >/dev/null 2>&1; then
  ok "Repositorio Git inicializado"
else
  bad "No hay repositorio Git"
fi

if [[ -n "$(git remote | head -1)" ]]; then
  ok "Hay remoto configurado: $(git remote | head -1) -> $(git remote get-url origin 2>/dev/null)"
else
  infra "Sin remoto: no es posible proteger ramas (git remote add origin <url> && git push -u origin main)"
fi

BRANCHES=$(git branch --all | wc -l)
if [[ "$BRANCHES" -gt 1 ]]; then
  ok "Existen ramas além de main ($BRANCHES referencias)"
else
  infra "Solo existe la rama main: falta flujo de ramas feature (git checkout -b feat/...)"
fi

if [[ -n "$REMOTE" ]] && command -v gh >/dev/null 2>&1; then
  if gh api "repos/$REMOTE/branches/main/protection" >/dev/null 2>&1; then
    ok "Protección de main verificada en el remoto"
  else
    bad "main SIN protección en $REMOTE (Settings -> Branches -> Add rule)"
  fi
else
  warn "Protección de ramas no verificable sin --remote OWNER/REPO y gh CLI"
fi

echo ""
echo "── Ítem 2: Estándares de commits (Conventional Commits) ──────────"
if [[ -f .pre-commit-config.yaml ]] && grep -q "conventional-pre-commit" .pre-commit-config.yaml; then
  ok "conventional-pre-commit configurado en .pre-commit-config.yaml"
else
  bad "Hook de commits convencionales no configurado"
fi

if [[ -x .git/hooks/commit-msg ]]; then
  ok "Hook commit-msg instalado en .git/hooks"
else
  bad "Hook commit-msg no instalado (pre-commit install --hook-type commit-msg)"
fi

BAD_COMMITS=0
while read -r subject; do
  if ! echo "$subject" | grep -qE '^(feat|fix|chore|docs|style|refactor|test|perf)(\(.+\))?!?:'; then
    BAD_COMMITS=$((BAD_COMMITS + 1))
    bad "Commit fuera de estándar: $subject"
  fi
done < <(git log --format=%s --all)
[[ "$BAD_COMMITS" -eq 0 ]] && ok "Todos los commits cumplen Conventional Commits ($(git log --oneline --all | wc -l) revisados)"

echo ""
echo "── Ítem 3: Variables de entorno y secretos ───────────────────────"
if git ls-files --error-unmatch .env.example >/dev/null 2>&1; then
  ok ".env.example versionado en el repo"
else
  bad ".env.example no está versionado"
fi

if git check-ignore -q .env; then
  ok ".env está ignorado por .gitignore"
else
  bad ".env NO está ignorado: el secreto entrará al repo"
fi

if [[ -n "$(git ls-files | grep -E '(^|/)\.env$')" ]]; then
  bad "¡¡Un archivo .env está tracked en Git!! Revísalo de inmediato"
else
  ok "Ningún archivo .env real está versionado"
fi

if git log --all -p -- .env 2>/dev/null | grep -q "SECRET_KEY"; then
  bad "El historial de Git contiene secretos de .env"
else
  ok "El historial de Git no contiene secretos"
fi

echo ""
echo "── Ítem 4: Linter y formateador (Ruff) ───────────────────────────"
if uv run ruff check . >/dev/null 2>&1; then
  ok "ruff check sin errores"
else
  bad "ruff check con errores (uv run ruff check .)"
fi

if uv run ruff format --check . >/dev/null 2>&1; then
  ok "ruff format sin cambios pendientes"
else
  bad "ruff format con archivos sin formatear (uv run ruff format .)"
fi

if uv run pre-commit run --all-files >/dev/null 2>&1; then
  ok "pre-commit run --all-files en verde"
else
  bad "pre-commit falla (uv run pre-commit run --all-files)"
fi

echo ""
echo "── Ítem 5: Hello World + CI/CD (modo: $MODE) ─────────────────────"
if [[ -f .github/workflows/ci.yml ]]; then
  ok "Workflow de CI presente (.github/workflows/ci.yml)"
else
  bad "No hay workflow de CI"
fi

if [[ -n "$(git remote)" ]] && command -v gh >/dev/null 2>&1; then
  LAST=$(gh run list --limit 1 --json conclusion,status --jq '.[0] | "\(.status)/\(.conclusion)"' 2>/dev/null)
  if [[ "$LAST" == "completed/success" ]]; then
    ok "Última ejecución de CI en GitHub: success"
  elif [[ -n "$LAST" ]]; then
    bad "Última ejecución de CI: $LAST"
  else
    warn "No se pudo consultar la CI de GitHub"
  fi
elif [[ "$MODE" == "local" ]]; then
  pend "CI de GitHub (pospuesta: aún no hay remoto)"
else
  bad "La CI nunca puede ejecutarse sin remoto + gh CLI"
fi

# --- Hello World ---
HEALTH_URL="${HEALTH_URL:-}"
PORT="${HEALTH_PORT:-8765}"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
  fi
}
trap cleanup EXIT

check_health() {
  # $1 = URL base, $2 = etiqueta para el mensaje
  local body
  body=$(curl -fsS --max-time 5 "$1/health/" 2>/dev/null)
  if echo "$body" | grep -q '"status": *"ok"'; then
    ok "Hello World responde en $2 -> $body"
    return 0
  fi
  bad "No responde en $2/health/ (obtuvo: ${body:-vacío})"
  return 1
}

if [[ -n "$HEALTH_URL" ]]; then
  check_health "$HEALTH_URL" "$HEALTH_URL"
elif [[ "$MODE" == "local" ]]; then
  echo "  · Levantando servidor local en 127.0.0.1:$PORT ..."
  uv run python manage.py runserver "127.0.0.1:$PORT" --noreload >/dev/null 2>&1 &
  SERVER_PID=$!

  READY=""
  for _ in $(seq 1 30); do
    if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/health/" >/dev/null 2>&1; then
      READY=1
      break
    fi
    sleep 1
  done

  if [[ -n "$READY" ]]; then
    check_health "http://127.0.0.1:$PORT" "http://127.0.0.1:$PORT (local)"
  else
    bad "El servidor local no respondió en 30s (uv run python manage.py runserver)"
  fi
  cleanup
  SERVER_PID=""
else
  bad "Sin URL de despliegue: exporta HEALTH_URL=https://tu-app para comprobar el Hello World"
fi

if pgrep -x gunicorn >/dev/null 2>&1 || pgrep -x nginx >/dev/null 2>&1; then
  ok "Servicios gunicorn/nginx activos en esta máquina"
elif [[ "$MODE" == "remote" ]]; then
  warn "No hay gunicorn/nginx corriendo localmente (correcto si el despliegue es remoto)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
printf 'Resultado: \033[32m%d PASS\033[0m · \033[31m%d FAIL\033[0m · \033[33m%d WARN\033[0m · \033[36m%d PEND\033[0m\n' "$PASS" "$FAIL" "$WARN" "$PEND"
if [[ "$FAIL" -eq 0 && "$PEND" -eq 0 ]]; then
  echo "Fase 2: EN OPERACIÓN ✅"
elif [[ "$FAIL" -eq 0 ]]; then
  echo "Fase 2 (modo $MODE): LOCALMENTE LISTA ✅  ·  quedan $PEND ítems de infraestructura pendientes"
  echo "  → pospuestos hasta que termines la app en local: CI en GitHub, ramas protegidas, despliegue"
else
  echo "Fase 2: INCOMPLETA ❌ ($FAIL ítems sin comprobar)"
fi
echo "════════════════════════════════════════════════════════════════"

# Los ítems pospuestos (PEND) no rompen el test: solo FAIL cuenta.
exit "$FAIL"
