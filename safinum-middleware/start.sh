#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-3000}"

NGROK_PID=""
cleanup() {
  if [[ -n "$NGROK_PID" ]]; then
    kill "$NGROK_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

if command -v ngrok >/dev/null 2>&1; then
  if ! curl -fsS http://127.0.0.1:4040/api/tunnels >/dev/null 2>&1; then
    ngrok http "$PORT" --log=stdout >/tmp/safinum_ngrok.log 2>&1 &
    NGROK_PID=$!
    for _ in $(seq 1 15); do
      TUNNEL_URL=$(curl -fsS http://127.0.0.1:4040/api/tunnels 2>/dev/null | ../.venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(next((t["public_url"] for t in d.get("tunnels",[]) if str(t.get("public_url","")).startswith("https://")),""))' 2>/dev/null || true)
      if [[ -n "${TUNNEL_URL:-}" ]]; then
        echo "================================================================="
        echo "  Safinum Lingua Studio public : ${TUNNEL_URL}/studio"
        echo "  Endpoint Sandbox /middleware : ${TUNNEL_URL}/middleware"
        echo "================================================================="
        break
      fi
      sleep 0.5
    done
  fi
fi

../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
