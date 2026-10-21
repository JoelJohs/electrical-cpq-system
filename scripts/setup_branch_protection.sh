#!/usr/bin/env bash
# ==============================================================================
# Script para configurar reglas de protección en la rama 'main' de GitHub
# Uso:
#   ./scripts/setup_branch_protection.sh [OWNER/REPO]
# Ejemplo:
#   ./scripts/setup_branch_protection.sh JoelJohs/electrical-cpq-system
# ==============================================================================
set -euo pipefail

REPO="${1:-JoelJohs/electrical-cpq-system}"

echo "=== Configurando Protección de Rama para $REPO (rama: main) ==="

if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: GitHub CLI ('gh') no está instalado." >&2
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "AVISO: No has iniciado sesión en GitHub CLI ('gh auth login')."
    echo "Puedes ejecutar: gh auth login --web"
    exit 1
fi

echo "Aplicando reglas de protección sobre 'main'..."
# Configuración mediante API de protección de ramas de GitHub:
# - Check obligatorio: 'lint-and-test'
# - Sin bloquear con revisiones obligatorias de terceros (ideal para desarrollo individual/MVP)
gh api --method PUT "repos/$REPO/branches/main/protection" \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "lint-and-test"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF

echo "Verificando estado de protección..."
gh api "repos/$REPO/branches/main/protection" --jq '.required_status_checks'

echo "=== Protección de rama 'main' configurada con éxito ==="
