#!/usr/bin/env bash
# Enregistre votre URL publique sur les 6 canaux du sandbox SAFINUM.
# Usage :
#   ./register_endpoints.sh [TEAM_KEY] [PUBLIC_HTTPS_URL]
# Si omis, lit depuis .env (SAFINUM_TEAM_KEY / SAFINUM_PUBLIC_URL).
set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .env ]]; then
  set -a; source .env; set +a
fi

TEAM_KEY="${1:-${SAFINUM_TEAM_KEY:-}}"
PUBLIC_URL="${2:-${SAFINUM_PUBLIC_URL:-}}"
API_BASE="${SAFINUM_BANK_API_URL:-https://www.safinum.cm/api/v1}"
API_BASE="${API_BASE%/}"
VENV_PYTHON="$(dirname "$0")/../.venv/bin/python"

if [[ -z "$TEAM_KEY" || -z "$PUBLIC_URL" ]]; then
  echo "Usage: $0 <TEAM_KEY> <PUBLIC_HTTPS_URL>"
  echo "Exemple: $0 sbx_votre_cle https://xxxx.ngrok-free.app"
  exit 1
fi

MIDDLEWARE_URL="${PUBLIC_URL%/}/middleware"

echo "Enregistrement de : $MIDDLEWARE_URL"
echo ""

for ch in ussd mobile web sms atm ivr; do
  resp=$(curl -s --max-time 8 -X POST "${API_BASE}/sandbox/endpoint" \
    -H "X-Team-Key: ${TEAM_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"channel\":\"${ch}\",\"url\":\"${MIDDLEWARE_URL}\"}" 2>/dev/null || echo '{}')
  status=$("$VENV_PYTHON" -c "
import json, sys
try:
    d = json.loads('''${resp}''')
    print('LOCKED' if d.get('locked') else ('OK' if not d.get('error') else 'ERREUR:'+str(d.get('error',''))))
except: print('?')
" 2>/dev/null || echo "?")
  printf "  %-8s -> %s\n" "[$ch]" "$status"
done

echo ""
echo "Configuration enregistrée :"
curl -s --max-time 5 "${API_BASE}/sandbox/endpoint" -H "X-Team-Key: ${TEAM_KEY}" \
  | "$VENV_PYTHON" -c "
import json,sys
try:
    d=json.load(sys.stdin)
    for ch,url in (d.get('endpoints') or {}).items(): print(f'  {ch:8s} -> {url}')
except: pass
" 2>/dev/null || true
echo ""
