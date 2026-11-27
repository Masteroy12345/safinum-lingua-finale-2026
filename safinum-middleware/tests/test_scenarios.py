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
from app.phonetics import _estimate_median_f0, _expand_numbers_for_tts, _prepare_elevenlabs_native_text, synthesize_wav_bytes, to_ipa, to_tts_script, to_web_phonetic_safe
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

    r_ewo = client.post("/middleware", json={
        "trace_id": "tr-1c", "channel": "ussd", "phone": "237677000001",
        "language": "ewo", "input": {"type": "text", "text": "Mòni wom a lig ma a ne tân ya?"},
    })
    assert r_ewo.json()["interpretation"]["intent"] == "BALANCE_INQUIRY"

    r_tr_ewo = client.post("/api/translate", json={"language": "ewo", "text": "Quel est mon solde disponible ?"})
    assert r_tr_ewo.status_code == 200
    assert r_tr_ewo.json()["translated"] == "Mòni wom a lig ma a ne tân ya?"


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

    for lang in ("fr", "en", "dua", "ewo", "bas", "bbj", "byv", "fub", "hau", "bum", "wes"):
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
    assert "francs céfa" in p.json()["tts_script"] or "francs séfa" in p.json()["tts_script"]


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


def test_banking_security_numbers_client_names_and_studio_endpoints(monkeypatch):
    # 1. Confidentialité stricte : les traductions ne contiennent AUCUNE somme, nom de client ni téléphone — uniquement des {variables} changeables
    from app.languages import FINANCIAL_TERMS, TEMPLATES, render_variables

    r_tr = client.post("/api/translate", json={
        "language": "dua",
        "text": "Bonjour Amina, envoyer 15 000 FCFA à Jean Mbarga au 677000002 (TRX-9042)",
    })
    assert r_tr.status_code == 200
    body = r_tr.json()
    tr = body["translated"]
    # Les valeurs confidentielles NE DOIVENT JAMAIS figurer dans la traduction :
    assert "15 000" not in tr and "15000" not in tr
    assert "Amina" not in tr
    assert "Jean Mbarga" not in tr
    assert "677000002" not in tr
    assert "TRX-9042" not in tr
    # Elles sont remplacées par des variables dynamiques modifiables :
    assert "{name}" in tr
    assert "{amount}" in tr
    assert "{beneficiary}" in tr
    assert "{phone}" in tr
    assert "{reference}" in tr
    assert body["variables"]["name"] == "Amina"
    assert body["variables"]["amount"] == "15 000 FCFA"
    assert body["variables"]["beneficiary"] == "Jean Mbarga"
    assert body["variables"]["phone"] == "677000002"
    assert body["variables"]["reference"] == "TRX-9042"
    # Et elles peuvent être injectées/modifiées dynamiquement côté client/audio :
    rendered_custom = render_variables(tr, {
        "name": "Amadou Kamga",
        "amount": "25 000 FCFA",
        "beneficiary": "Paul Sali",
        "phone": "237653633039",
        "reference": "TRX-1111",
    })
    assert "Amadou Kamga" in rendered_custom and "25 000 FCFA" in rendered_custom and "Paul Sali" in rendered_custom

    # 1b. Aucun gabarit statique (UI_TRANSLATIONS, TEMPLATES hors menus 1/2/0, FINANCIAL_TERMS) ne contient de téléphone ni somme en dur
    phone_re = re.compile(r"(?:\+?237[\s\-\.]?)?[26](?:[\s\-\.]?\d){8}\b")
    sum_re = re.compile(r"\b\d[\d\s\.,]*\s*(?:FCFA|XAF|CFA)\b", re.IGNORECASE)
    for lg, table in UI_TRANSLATIONS.items():
        for k, val in table.items():
            assert not phone_re.search(val), f"Numéro en dur interdit dans UI {lg}.{k}: {val}"
            assert not sum_re.search(val), f"Somme en dur interdite dans UI {lg}.{k}: {val}"
    for lg, table in TEMPLATES.items():
        for k, val in table.items():
            assert not phone_re.search(val), f"Numéro en dur interdit dans TEMPLATES {lg}.{k}: {val}"
            # retire d'abord les variables {amount} FCFA légitimes avant de vérifier qu'aucun chiffre suivi de FCFA n'est codé en dur
            assert not sum_re.search(val), f"Somme en dur interdite dans TEMPLATES {lg}.{k}: {val}"
    for term_k, table in FINANCIAL_TERMS.items():
        for lg, val in table.items():
            assert not phone_re.search(val), f"Numéro en dur interdit dans FINANCIAL_TERMS {term_k}.{lg}: {val}"
            assert not sum_re.search(val), f"Somme en dur interdite dans FINANCIAL_TERMS {term_k}.{lg}: {val}"

    # 2. Studio web type Google Traduction + comparateur 9 langues + 89 clés UI + enregistrements natifs
    st_html = client.get("/studio")
    assert st_html.status_code == 200
    assert "{name}" in st_html.text and "{amount}" in st_html.text
    r_all = client.post("/api/translate-all", json={"text": "Bonjour Amina, envoyer 5 000 FCFA"})
    assert r_all.status_code == 200
    for lg_code, item in r_all.json()["translations"].items():
        assert "Amina" not in item["translated"] and "5 000" not in item["translated"]
        assert "{name}" in item["translated"] and "{amount}" in item["translated"]
    ui_k = client.get("/api/ui-keys?language=ewo")
    assert ui_k.status_code == 200
    assert ui_k.json()["count"] == 89
    nat = client.get("/api/native-recordings")
    assert nat.status_code == 200
    assert nat.json()["count"] >= 1

    # 3. Sélection d'homonymes par numéro ("1" ou "2") en USSD sans déclencher Solde/Transfert
    monkeypatch.setattr(
        bank_client,
        "search_beneficiaries",
        AsyncMock(return_value={"beneficiaries": [
            {"name": "Jean Mbarga", "phone": "237677000010"},
            {"name": "Jean Atangana", "phone": "237677000011"},
        ]}),
    )
    r_amb = client.post("/middleware", json={
        "trace_id": "tr-amb-1", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "text", "text": "envoyer 5000 FCFA à Jean"},
    })
    assert r_amb.json()["interpretation"]["intent"] == "CLARIFICATION_NEEDED"
    r_pick = client.post("/middleware", json={
        "trace_id": "tr-amb-2", "channel": "ussd", "phone": "237677000001",
        "language": "fr", "input": {"type": "menu", "text": "2"},
    })
    b_pick = r_pick.json()
    assert b_pick["interpretation"]["intent"] == "TRANSFER"
    assert b_pick["transaction"]["status"] == "pending"
    assert b_pick["interpretation"]["parameters"]["to"] == "237677000011"


def test_audio_french_proper_nouns_raw_numbers_fcfa_and_cross_channel_ui_lang():
    # 1. Noms propres (Jean Mbarga, Amina) intacts (jamais Mebarga), FCFA lu en français fluide (jamais épellation C F A)
    script = to_tts_script("Bonjour Amina, envoyer 15 000 FCFA à Jean Mbarga", "dua")
    assert "Jean Mbarga" in script
    assert "Mebarga" not in script
    assert "Amina" in script
    assert "francs céfa" in script.lower()
    assert "C F A" not in script
    assert "15 000" in script
    assert "quinze mille" in _expand_numbers_for_tts(script).lower()

    # 1b. Le flux natif ElevenLabs conserve le texte natif et décompose DYNAMIQUEMENT tout numéro variable sans avaler les zéros
    native_el = _prepare_elevenlabs_native_text("Idib'a bwam Amina, lóma 15 000 FCFA na Jean Mbarga o 677000002")
    assert "Idib'a bwam Amina" in native_el
    assert "15 000 francs CFA" in native_el
    assert "Jean Mbarga" in native_el
    assert "6, 77, zéro zéro, zéro zéro, zéro 2" in native_el
    native_var_phone = _prepare_elevenlabs_native_text("Compte +237 657 09 64 50 et 699050041")
    assert "+237, 6, 57, zéro 9, 64, 50" in native_var_phone
    assert "6, 99, zéro 5, zéro zéro, 41" in native_var_phone

    # 2. Synthèse WAV homme uniquement (F0 <= 150 Hz) via endpoint et module phonetics
    wav, model_name = synthesize_wav_bytes("Amina envoie 5 000 FCFA à Jean Mbarga.", "ewo")
    assert wav is not None and wav[:4] == b"RIFF"
    assert model_name == "elevenlabs-brian-male" or model_name.startswith("mms-tts-fra")
    import io
    import wave
    import numpy as np
    with wave.open(io.BytesIO(wav), "rb") as wf:
        sr = wf.getframerate()
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    f0 = _estimate_median_f0(pcm, sr)
    assert f0 is None or f0 <= 150.0, f"F0 trop aigu ({f0} Hz) : doit être une voix d'homme"

    r_wav = client.post("/api/audio/tts", json={"text": "Bonjour Jean Mbarga, 5 000 FCFA", "language": "bas"})
    assert r_wav.status_code == 200
    assert r_wav.headers["content-type"].startswith("audio/wav")
    assert r_wav.content[:4] == b"RIFF"

    # 3. Continuité multicanal (ui_translation avec language=None conserve la langue USSD de session)
    r_ussd = client.post("/middleware", json={
        "trace_id": "tr-cross-1", "channel": "ussd", "phone": "237677000099",
        "language": "dua", "input": {"type": "text", "text": "solde"},
    })
    assert r_ussd.status_code == 200
    assert r_ussd.json()["interpretation"]["language"] == "dua"

    r_mob = client.post("/middleware", json={
        "trace_id": "tr-cross-2",
        "channel": "mobile",
        "type": "ui_translation",
        "phone": "237677000099",
        "language": None,
        "screen": "home",
        "strings": {
            "nav.home": {"text": "Accueil", "max_chars": 12},
            "home.balance_label": {"text": "Solde disponible"},
        },
    })
    assert r_mob.status_code == 200
    mob_body = r_mob.json()
    assert mob_body["language"] == "dua"
    assert mob_body["strings"]["nav.home"] != "Accueil"


def test_soreva_native_voice_bank_all_7_cameroonian_languages_and_male_sts():
    from app.native_voice_bank import apply_native_tonality, get_language_voice_settings

    r_bank = client.get("/api/native-bank?language=ewo")
    assert r_bank.status_code == 200
    b_data = r_bank.json()
    stats = b_data["stats"]
    for lang_code in ("ewo", "dua", "bas", "bbj", "byv", "fub", "wes"):
        assert stats.get(lang_code, 0) == 150, f"Dataset SOREVA incomplet pour {lang_code}"
    assert b_data["count"] == 150

    # 1. Transfert de la tonalité SOREVA sur le texte (sans mélanger deux audios ni jouer les WAV du dataset)
    toned_ewo = apply_native_tonality("mbembe kidi", "ewo")
    assert "mbəmbə" in toned_ewo and "kídí" in toned_ewo
    vs = get_language_voice_settings("ewo")
    assert 0.45 <= vs["stability"] <= 0.65

    # 2. Protection des noms propres, chiffres et FCFA + lecture normale du téléphone lors de l'injection de tonalité
    el_txt = _prepare_elevenlabs_native_text("Idib'a bwam Amina, lóma 15 000 FCFA na Jean Mbarga o 677000002", "dua")
    assert "Amina" in el_txt and "Jean Mbarga" in el_txt
    assert "15 000 francs CFA" in el_txt and "6, 77, zéro zéro, zéro zéro, zéro 2" in el_txt

    # 3. Flux audio 100% unique (jamais deux audios mélangés)
    wav_nat, eng_nat = synthesize_wav_bytes("mbembe kidi", "ewo")
    assert wav_nat is not None and wav_nat[:4] == b"RIFF"
    assert eng_nat == "elevenlabs-brian-male" or eng_nat.startswith("mms-tts-fra")
    assert "mix" not in eng_nat and "soreva-native" not in eng_nat


def test_hausa_gsm7_atm_5000_multiples_and_airtime_operator_without_to():
    # 1. Translittération GSM-7 stricte des caractères Haoussa (ƙ, ɓ, ɗ, ƴ) et Ghomala (ʼ)
    h_clean = transliterate_to_gsm7("Kuɗi ƙasa ɓoye ƴaʼƴa 5 000 FCFA")
    assert is_gsm7(h_clean)
    assert "Kudi kasa boye ya'ya" in h_clean

    # 2. GAB/ATM : rejet d'un montant non multiple de 5 000 FCFA puis acceptation d'un multiple de 5 000 FCFA
    r_atm1 = client.post("/middleware", json={
        "trace_id": "tr-atm-1", "channel": "atm", "phone": "237657096450",
        "language": "hau", "input": {"type": "keypad", "text": "cire kudi 3000 FCFA"},
    })
    assert r_atm1.status_code == 200
    assert r_atm1.json()["interpretation"]["intent"] == "CLARIFICATION_NEEDED"

    r_atm2 = client.post("/middleware", json={
        "trace_id": "tr-atm-2", "channel": "atm", "phone": "237657096450",
        "language": "hau", "input": {"type": "keypad", "text": "10000"},
    })
    b_atm2 = r_atm2.json()
    assert b_atm2["interpretation"]["intent"] == "TRANSFER"
    assert b_atm2["interpretation"]["parameters"]["type"] == "withdrawal"
    assert b_atm2["transaction"]["status"] == "pending"

    # 3. Crédit téléphonique avec opérateur explicite sans numéro destinataire -> envoie `operator` sans `to` contradictoire
    r_air = client.post("/middleware", json={
        "trace_id": "tr-air-op", "channel": "ussd", "phone": "237657096450",
        "language": "fr", "input": {"type": "text", "text": "acheter 1000 FCFA de crédit MTN"},
    })
    assert r_air.status_code == 200
    call_payload = bank_client.create_transaction.call_args[0][0]
    assert call_payload["type"] == "airtime"
    assert call_payload["operator"] == "MTN"
    assert "to" not in call_payload
