#!/usr/bin/env bash
# ============================================================
# Safinum Lingua — Script de démarrage complet
# 1. Charge les variables d'environnement (.env)
# 2. Lance ngrok si nécessaire (ou réutilise le tunnel existant)
# 3. Enregistre l'URL /middleware sur les 6 canaux du sandbox
# 4. Lance le middleware FastAPI
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

# ── Charger .env ────────────────────────────────────────────
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PORT="${PORT:-3000}"
TEAM_KEY="${SAFINUM_TEAM_KEY:-}"
API_BASE="${SAFINUM_BANK_API_URL:-https://www.safinum.cm/api/v1}"
API_BASE="${API_BASE%/}"

VENV_PYTHON="$(dirname "$0")/../.venv/bin/python"
VENV_UVICORN="$(dirname "$0")/../.venv/bin/uvicorn"

# ── Nettoyage à la sortie ────────────────────────────────────
NGROK_PID=""
cleanup() {
  [[ -n "$NGROK_PID" ]] && kill "$NGROK_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

# ── Obtenir ou démarrer ngrok ─────────────────────────────────
get_ngrok_url() {
  "$VENV_PYTHON" - <<'PY'
import json, sys
try:
    import urllib.request
    with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=3) as r:
        d = json.load(r)
    url = next((t["public_url"] for t in d.get("tunnels", [])
                if t.get("public_url", "").startswith("https://")), "")
    print(url, end="")
except Exception:
    print("", end="")
PY
}

TUNNEL_URL=""

if command -v ngrok >/dev/null 2>&1; then
  # Essayer d'abord un tunnel déjà actif
  TUNNEL_URL=$(get_ngrok_url)

  if [[ -z "$TUNNEL_URL" ]]; then
    echo "[ngrok] Démarrage du tunnel sur le port $PORT..."
    ngrok http "$PORT" --log=stdout > /tmp/safinum_ngrok.log 2>&1 &
    NGROK_PID=$!

    # Attendre jusqu'à 15s que le tunnel soit actif
    for _ in $(seq 1 30); do
      TUNNEL_URL=$(get_ngrok_url)
      [[ -n "$TUNNEL_URL" ]] && break
      sleep 0.5
    done
  fi

  if [[ -n "$TUNNEL_URL" ]]; then
    echo ""
    echo "================================================================="
    echo "  Tunnel public    : $TUNNEL_URL"
    echo "  Endpoint sandbox : $TUNNEL_URL/middleware"
    echo "================================================================="
  else
    echo "[ngrok] Tunnel non disponible après 15s."
  fi
else
  echo "[INFO] ngrok introuvable dans le PATH."
fi

# ── Enregistrer l'URL sur le sandbox (tous les 6 canaux) ─────
register_endpoints() {
  local base_url="$1"
  local mw_url="${base_url%/}/middleware"

  if [[ -z "$TEAM_KEY" ]]; then
    echo "[SKIP] SAFINUM_TEAM_KEY absent — enregistrement ignoré."
    return
  fi

  echo ""
  echo "[sandbox] Enregistrement de $mw_url sur les 6 canaux..."
  for ch in ussd mobile web sms atm ivr; do
    resp=$(curl -s --max-time 8 -X POST "${API_BASE}/sandbox/endpoint" \
      -H "X-Team-Key: ${TEAM_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"channel\":\"${ch}\",\"url\":\"${mw_url}\"}" 2>/dev/null || echo '{"error":"timeout"}')

    # Extraire le statut (locked ou saved) depuis la réponse JSON
    status=$("$VENV_PYTHON" -c "
import json, sys
try:
    d = json.loads('''${resp}''')
    if d.get('error'):
        print('ERREUR:', d['error'])
    elif d.get('locked'):
        print('LOCKED (évaluation en cours)')
    else:
        print('OK')
except Exception as e:
    print('?', str(e)[:40])
" 2>/dev/null || echo "?")

    printf "  %-8s -> %s\n" "[$ch]" "$status"
  done

  # Vérification finale
  echo ""
  echo "[sandbox] Configuration enregistrée :"
  curl -s --max-time 5 "${API_BASE}/sandbox/endpoint" \
    -H "X-Team-Key: ${TEAM_KEY}" 2>/dev/null \
    | "$VENV_PYTHON" -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for ch, url in (d.get('endpoints') or {}).items():
        print(f'  {ch:8s} -> {url}')
except Exception:
    pass
" 2>/dev/null || true
  echo ""
}

if [[ -n "$TUNNEL_URL" ]]; then
  register_endpoints "$TUNNEL_URL"
elif [[ -n "${SAFINUM_PUBLIC_URL:-}" ]]; then
  echo "[INFO] Utilisation de SAFINUM_PUBLIC_URL=$SAFINUM_PUBLIC_URL"
  register_endpoints "$SAFINUM_PUBLIC_URL"
else
  echo "[WARN] Aucune URL publique disponible — enregistrement ignoré."
  echo "       Relancez avec : SAFINUM_PUBLIC_URL=https://xxxx.ngrok-free.app bash start.sh"
fi

# ── Démarrer le middleware FastAPI ───────────────────────────
echo ""
echo "[middleware] Démarrage sur http://0.0.0.0:$PORT ..."
exec "$VENV_UVICORN" app.main:app --host 0.0.0.0 --port "$PORT" --reload
