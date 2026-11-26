#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "Demarrage des 3 services SAFINUM Lingua (Dev space ICT)..."
echo "  - Middleware Principal (USSD + Mobile/Web UI) : http://localhost:3000"
echo "  - Service IA Traduction + Correction T5       : http://localhost:3001"
echo "  - Traduction Lexicale Mot-a-Mot               : http://localhost:3002"

(cd safinum-middleware && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3000) &
PID1=$!
(cd traduction_service_google && ../.venv/bin/uvicorn app:app --host 0.0.0.0 --port 3001) &
PID2=$!
(cd traduction_mot_a_mot && ../.venv/bin/uvicorn app:app --host 0.0.0.0 --port 3002) &
PID3=$!

trap "kill $PID1 $PID2 $PID3 2>/dev/null || true" EXIT INT TERM
wait
