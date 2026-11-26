#!/usr/bin/env bash
# Enregistre votre URL publique HTTPS (ngrok / cloudflared) auprès du sandbox SAFINUM
# pour les 3 canaux obligatoires (ussd, mobile, web).
# Usage :
#   ./register_endpoints.sh <TEAM_KEY> <PUBLIC_HTTPS_URL>
# Exemple :
#   ./register_endpoints.sh sbx_votre_cle https://xxxx.ngrok-free.app
set -euo pipefail

TEAM_KEY="${1:-${SAFINUM_TEAM_KEY:-}}"
PUBLIC_URL="${2:-${SAFINUM_PUBLIC_URL:-}}"
API_BASE="${SAFINUM_BANK_API_URL:-https://www.safinum.cm/api/v1}"
API_BASE="${API_BASE%/}"

if [[ -z "$TEAM_KEY" && -f "$(dirname "$0")/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$(dirname "$0")/.env"
  set +a
  TEAM_KEY="${TEAM_KEY:-${SAFINUM_TEAM_KEY:-}}"
fi

if [[ -z "$TEAM_KEY" || -z "$PUBLIC_URL" ]]; then
  echo "Usage: $0 <TEAM_KEY> <PUBLIC_HTTPS_URL>"
  echo "Exemple: $0 sbx_votre_cle https://votre-tunnel.trycloudflare.com"
  exit 1
fi

BASE="${PUBLIC_URL%/}"
MIDDLEWARE_URL="${BASE}/middleware"

echo "Vérification locale de /health sur ${BASE}/health ..."
if curl -fsS -m 5 "${BASE}/health" >/dev/null 2>&1; then
  echo "  [OK] Middleware joignable publiquement."
else
  echo "  [INFO] ${BASE}/health non joignable pour l'instant (vérifiez uvicorn + tunnel HTTPS)."
fi

for ch in ussd mobile web; do
  echo "Enregistrement du canal [$ch] -> $MIDDLEWARE_URL ..."
  curl -fsSL -X POST "${API_BASE}/sandbox/endpoint" \
    -H "X-Team-Key: ${TEAM_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"channel\":\"${ch}\",\"url\":\"${MIDDLEWARE_URL}\"}"
  echo ""
done

echo ""
echo "Vérification de la configuration enregistrée sur ${API_BASE}/sandbox/endpoint :"
curl -fsSL "${API_BASE}/sandbox/endpoint" -H "X-Team-Key: ${TEAM_KEY}"
echo ""
