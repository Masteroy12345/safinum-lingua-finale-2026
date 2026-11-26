"""Suite de tests automatisés couvrant 100% du contrat SAFINUM 2026 (USSD + Mobile/Web UI + 10 Scénarios + Phonétique + GSM-7)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.bank_client import BankApiError
from app.gsm7 import is_gsm7, septet_length, transliterate_to_gsm7
from app.main import app, bank_client
from app.phonetics import to_ipa, to_tts_script, to_web_phonetic_safe
from app.session_store import store
from app.ui_translator import UI_TRANSLATIONS

client = TestClient(app)
_PH_RE = re.compile(r"\{[a-z_]+\}")


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    store._by_phone.clear()
    store._diagnostics.clear()
    monkeypatch.setattr(bank_client, "get_account", AsyncMock(return_value={"holder_name": "Amina", "balance": 250000, "currency": "XAF"}))
    monkeypatch.setattr(bank_client, "get_fees", AsyncMock(return_value={"fee": 50, "total": 5050}))
    monkeypatch.setattr(bank_client, "get_transactions", AsyncMock(return_value={"transactions": [{"type": "transfer", "amount": 10000, "to": "237677000002"}]}))
    monkeypatch.setattr(bank_client, "create_transaction", AsyncMock(return_value={"id": "TRX-9001", "fee": 50, "total": 5050, "operator": "MTN"}))
    monkeypatch.setattr(bank_client, "update_transaction", AsyncMock(return_value={"id": "TRX-9001", "amount": 10000, "fee": 150, "total": 10150}))
    monkeypatch.setattr(bank_client, "confirm_transaction", AsyncMock(return_value={"id": "TRX-9001", "status": "confirmed"}))
    monkeypatch.setattr(bank_client, "cancel_transaction", AsyncMock(return_value={"id": "TRX-9001", "status": "cancelled"}))
    monkeypatch.setattr(bank_client, "search_beneficiaries", AsyncMock(return_value={"beneficiaries": [{"name": "Paul Biya Jr", "phone": "237677000003"}]}))


def test_gsm7_septets_and_transliteration():
    assert septet_length("10€") == 4
    raw = "Ɓasaá ɛ ɔ ŋ ə — café"
    clean = transliterate_to_gsm7(raw)
    assert is_gsm7(clean)
    assert "B" in clean and "ng" in clean


def test_scenario_1_balance_ussd_ewondo_and_without_word_solde():
    r = client.post("/middleware", json={
        "trace_id": "tr-1", "channel": "ussd", "phone": "237677000001",
        "language": "ewo", "input": {"type": "menu", "text": "1"},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["interpretation"]["intent"] == "BALANCE_INQUIRY"
    assert "250 000" in body["response"]["text"]
    assert is_gsm7(body["response"]["text"])
    assert septet_length(body["response"]["text"]) <= 182

    r_free = client.post("/middleware", json={
        "trace_id": "tr-1b", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "combien il me reste"},
    })
    assert r_free.json()["interpretation"]["intent"] == "BALANCE_INQUIRY"


def test_scenario_2_and_9_two_turn_cross_channel_transfer_and_options_strings():
    r1 = client.post("/middleware", json={
        "trace_id": "tr-init", "channel": "ussd", "phone": "677000001",
        "language": "fub", "input": {"type": "text", "text": "nel 5000 FCFA e 677000002"},
    })
    b1 = r1.json()
    assert b1["interpretation"]["intent"] == "TRANSFER"
    assert b1["transaction"]["status"] == "pending"
    assert b1["transaction"]["id"] == "TRX-9001"
    assert all(isinstance(o, str) for o in b1["response"]["options"])

    # Garde-fou : refuser confirmation sur le même trace_id
    r_same = client.post("/middleware", json={
        "trace_id": "tr-init", "channel": "ussd", "phone": "237677000001",
        "language": "fub", "input": {"type": "text", "text": "1"},
    })
    assert r_same.json()["transaction"]["status"] != "confirmed"

    # Tour 2 avec nouveau trace_id
    r2 = client.post("/middleware", json={
        "trace_id": "tr-confirm", "channel": "mobile", "phone": "237677000001",
        "language": "fub", "input": {"type": "text", "text": "tabbitin"},
    })
    b2 = r2.json()
    assert b2["interpretation"]["intent"] == "CONFIRM"
    assert b2["transaction"]["status"] == "confirmed"


def test_scenario_3_fees_and_4_history():
    r3 = client.post("/middleware", json={
        "trace_id": "tr-3", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "quels sont les frais pour 5000"},
    })
    assert r3.json()["interpretation"]["intent"] == "FEE_INQUIRY"

    r4 = client.post("/middleware", json={
        "trace_id": "tr-4", "channel": "ussd", "phone": "237677000001",
        "language": "en", "input": {"type": "text", "text": "show my transaction history"},
    })
    assert r4.json()["interpretation"]["intent"] == "TRANSACTION_HISTORY"


def test_scenario_5_correction_before_confirm():
    client.post("/middleware", json={
        "trace_id": "tr-5a", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "envoyer 5000 FCFA à 677000002"},
    })
    r5b = client.post("/middleware", json={
        "trace_id": "tr-5b", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "modifier le montant à 10000"},
    })
    assert r5b.json()["interpretation"]["intent"] == "CORRECTION"
    assert r5b.json()["transaction"]["status"] == "pending"


def test_scenario_6_ambiguous_bare_beneficiary_and_7_insufficient_funds(monkeypatch):
    r6 = client.post("/middleware", json={
        "trace_id": "tr-6", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "envoyer 5000 FCFA"},
    })
    assert r6.json()["interpretation"]["intent"] == "CLARIFICATION_NEEDED"

    # Réponse avec juste le prénom sans préposition
    r6b = client.post("/middleware", json={
        "trace_id": "tr-6b", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "Paul"},
    })
    assert r6b.json()["interpretation"]["intent"] == "TRANSFER"
    assert r6b.json()["transaction"]["status"] == "pending"

    monkeypatch.setattr(bank_client, "create_transaction", AsyncMock(side_effect=BankApiError(422, "INSUFFICIENT_FUNDS")))
    r7 = client.post("/middleware", json={
        "trace_id": "tr-7", "channel": "ussd", "phone": "237677000001",
        "language": "wes", "input": {"type": "text", "text": "send 400000 FCFA give 677000002"},
    })
    b7 = r7.json()
    assert b7["transaction"]["status"] == "failed"
    assert "INSUFFICIENT_FUNDS" not in b7["response"]["text"]


def test_scenario_8_language_switch_and_10_terminology_and_null_lang():
    r8 = client.post("/middleware", json={
        "trace_id": "tr-8", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "passer en duala"},
    })
    assert r8.json()["interpretation"]["intent"] == "LANGUAGE_SWITCH"
    assert r8.json()["interpretation"]["language"] == "dua"

    r10 = client.post("/middleware", json={
        "trace_id": "tr-10", "channel": "ussd", "phone": "237677000001",
        "language": None, "input": {"type": "text", "text": "c'est quoi les frais ?"},
    })
    assert r10.json()["interpretation"]["intent"] == "TERM_EXPLANATION"
    assert r10.json()["interpretation"]["language"] == "fr"


def test_mobile_web_ui_translation_contract_all_89_keys_9_languages():
    fr_keys = UI_TRANSLATIONS["fr"]
    assert len(fr_keys) == 89

    max_limits = {
        "nav.home": 12, "nav.transfer": 12, "nav.pay": 12, "nav.history": 12,
        "common.back": 20, "common.cancel": 20, "common.continue": 24, "common.listen": 20, "common.stop_listening": 24,
        "home.action_transfer": 28, "home.action_bill": 28, "home.action_airtime": 28, "home.action_history": 28,
        "home.see_all": 20,
        "tx.status.confirmed": 16, "tx.status.pending": 16, "tx.status.failed": 16, "tx.status.cancelled": 16,
    }

    payload_strings = {
        k: {"text": v, "context": "test", "max_chars": max_limits.get(k)}
        for k, v in fr_keys.items()
    }

    for lang in ("fr", "en", "dua", "ewo", "bas", "bbj", "byv", "fub", "wes"):
        resp = client.post("/middleware", json={
            "trace_id": f"ui-{lang}",
            "channel": "web",
            "type": "ui_translation",
            "phone": "237677000001",
            "language": lang,
            "source_language": "fr",
            "screen": "home",
            "strings": payload_strings,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == lang
        out_strings = data["strings"]
        assert set(out_strings.keys()) == set(fr_keys.keys())

        same_as_fr = 0
        for k, src_txt in fr_keys.items():
            tr_txt = out_strings[k]
            assert isinstance(tr_txt, str) and len(tr_txt.strip()) > 0
            assert set(_PH_RE.findall(src_txt)) == set(_PH_RE.findall(tr_txt)), f"Placeholder broken {lang}.{k}"
            if k in max_limits:
                assert len(tr_txt) <= max_limits[k], f"Over limit {lang}.{k}: {len(tr_txt)} > {max_limits[k]} ({tr_txt})"
            if tr_txt == src_txt:
                same_as_fr += 1

        if lang != "fr":
            assert same_as_fr / len(fr_keys) < 0.25, f"Too many untranslated keys in {lang}"


def test_phonetics_web_tts_and_ipa():
    ipa = to_ipa("Kɛl i lam. Ŋkap 5 000 FCFA.", "bas")
    assert ipa.startswith("/")
    web_txt = to_web_phonetic_safe("Kɛl i lam. Ŋkap bu {amount}", "bbj")
    assert "{amount}" in web_txt
    assert "ɛ" not in web_txt and "ŋ" not in web_txt.lower()

    p = client.post("/api/phonetics", json={"language": "bas", "text": "Kɛl i lam. U nlémèl 5 000 FCFA."})
    assert p.status_code == 200
    assert "francs C F A" in p.json()["tts_script"] or "francs CFA" in p.json()["tts_script"]


def test_fee_inquiry_asks_amount_without_guessing_and_uses_bank_fee():
    # Sans montant explicite -> clarification au lieu d'inventer 5000 FCFA
    r1 = client.post("/middleware", json={
        "trace_id": "tr-fee-1", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "quels sont les frais ?"},
    })
    assert r1.status_code == 200
    assert r1.json()["interpretation"]["intent"] == "CLARIFICATION_NEEDED"

    # Tour 2 : l'utilisateur fournit le montant -> appel API bancaire get_fees
    r2 = client.post("/middleware", json={
        "trace_id": "tr-fee-2", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "5000"},
    })
    b2 = r2.json()
    assert b2["interpretation"]["intent"] == "FEE_INQUIRY"
    assert b2["interpretation"]["parameters"]["fee"] == 50
    assert b2["interpretation"]["parameters"]["total"] == 5050


def test_airtime_and_bill_payment_multiturn_flows():
    # Achat de crédit sans montant -> clarification -> montant
    r_air1 = client.post("/middleware", json={
        "trace_id": "tr-air-1", "channel": "ussd", "phone": "237677000001",
        "language": "ewo", "input": {"type": "text", "text": "acheter credit MTN"},
    })
    assert r_air1.json()["interpretation"]["intent"] == "CLARIFICATION_NEEDED"

    r_air2 = client.post("/middleware", json={
        "trace_id": "tr-air-2", "channel": "ussd", "phone": "237677000001",
        "language": "ewo", "input": {"type": "text", "text": "2000"},
    })
    assert r_air2.json()["interpretation"]["intent"] == "AIRTIME_PURCHASE"
    assert r_air2.json()["transaction"]["status"] == "pending"

    # Paiement facture ENEO -> montant -> confirmation
    r_bill = client.post("/middleware", json={
        "trace_id": "tr-bill-1", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "payer ma facture ENEO 12000 FCFA"},
    })
    assert r_bill.json()["interpretation"]["intent"] == "BILL_PAYMENT"
    assert r_bill.json()["transaction"]["status"] == "pending"


def test_cross_channel_confirm_recovers_pending_tx_from_bank(monkeypatch):
    # Simulation d'un redémarrage session / cross-canal : session locale vide mais banque a une pending tx
    monkeypatch.setattr(
        bank_client,
        "get_transactions",
        AsyncMock(return_value={"transactions": [{"id": "TRX-EXT-77", "type": "transfer", "amount": 15000, "status": "pending", "to": "237677000002"}]}),
    )
    monkeypatch.setattr(
        bank_client,
        "confirm_transaction",
        AsyncMock(return_value={"id": "TRX-EXT-77", "status": "confirmed", "amount": 15000, "currency": "XAF"}),
    )
    r = client.post("/middleware", json={
        "trace_id": "tr-ext-conf", "channel": "mobile", "phone": "237699112233",
        "language": "fr", "input": {"type": "text", "text": "confirmer"},
    })
    b = r.json()
    assert b["interpretation"]["intent"] == "CONFIRM"
    assert b["transaction"]["id"] == "TRX-EXT-77"
    assert b["transaction"]["status"] == "confirmed"
    assert "15 000" in b["response"]["text"]
