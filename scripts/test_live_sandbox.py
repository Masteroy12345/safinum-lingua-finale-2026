"""Test d'intégration réel contre l'environnement SAFINUM Sandbox (aucun montant codé en dur).

Lit `SAFINUM_TEAM_KEY`, `SAFINUM_BANK_API_URL`, `SAFINUM_TEST_PHONE`, etc. depuis `.env` ou l'environnement.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT / "safinum-middleware" / ".env", override=False)

sys.path.insert(0, str(ROOT / "safinum-middleware"))
from fastapi.testclient import TestClient  # noqa: E402
from app.bank_client import BankApiError, BankClient  # noqa: E402
from app.main import app  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Test d'intégration SAFINUM Sandbox")
    parser.add_argument("--phone", default=os.getenv("SAFINUM_TEST_PHONE", "237677000001"))
    parser.add_argument("--amount", type=int, default=int(os.getenv("SAFINUM_TEST_AMOUNT", "0")))
    parser.add_argument("--to", default=os.getenv("SAFINUM_TEST_TO", ""))
    args = parser.parse_args()

    team_key = os.getenv("SAFINUM_TEAM_KEY", "")
    base_url = os.getenv("SAFINUM_BANK_API_URL", "https://www.safinum.cm/api/v1").rstrip("/")
    if not team_key or team_key.startswith("sbx_votre"):
        print("SAFINUM_TEAM_KEY non renseignée dans .env : exécutez avec votre vraie clé équipe pour le test live.")
        return 0

    client = TestClient(app)
    h = client.get("/health")
    assert h.status_code == 200
    print("Middleware health:", h.json()["status"], "| Bank API:", base_url)

    async def _probe_bank() -> None:
        bk = BankClient()
        trace = f"probe-{uuid.uuid4().hex[:8]}"
        acct = await bk.get_account(args.phone, trace, base_url)
        print("Compte sandbox (environnement):", acct)
        txs = await bk.get_transactions(args.phone, 5, trace, base_url)
        print("Transactions récentes:", len(txs.get("transactions") or txs.get("data") or []))

        if args.amount > 0:
            fees = await bk.get_fees("transfer", args.amount, f"fee-{uuid.uuid4().hex[:8]}", base_url)
            print(f"Frais renvoyés par la banque pour {args.amount}:", fees)

    try:
        asyncio.run(_probe_bank())
    except BankApiError as err:
        print(f"Erreur API bancaire ({err.status_code}): {err.code}")
        return 1

    # Vérifier le contrat /middleware USSD (solde lu depuis l'API bancaire)
    r = client.post("/middleware", json={
        "trace_id": f"sbx-{uuid.uuid4().hex[:8]}",
        "channel": "ussd",
        "phone": args.phone,
        "language": "fr",
        "input": {"type": "text", "text": "quel est mon solde ?"},
    })
    print("Réponse USSD /middleware:", r.status_code, r.json())
    assert r.status_code == 200
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
