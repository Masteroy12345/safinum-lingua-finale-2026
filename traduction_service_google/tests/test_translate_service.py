"""Tests complets du Service IA de Traduction & Correction de phrases entières (T5 + CTranslate2 + OPUS-MT + MMS-TTS)."""
from fastapi.testclient import TestClient

from app import app
from local_nmt import available_models_status

client = TestClient(app)


def test_service_health_and_models_present():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    models = data["models"]
    assert models["cameroon_int8"] is True
    assert models["opus_mt_bnt"] is True
    assert models["opus_mt_mul"] is True
    assert models["t5_spell_fr"] is True
    assert models["t5_grammar_en"] is True


def test_sentence_correction_fr_and_en_preserves_financial_entities():
    r_fr = client.post("/correct", json={
        "text": "bonjor Amina je veu envoye 5 000 FCFA a 677000001",
        "language": "fr",
    })
    assert r_fr.status_code == 200
    d_fr = r_fr.json()
    assert "{amount}" in d_fr["corrected"] and "5 000" not in d_fr["corrected"]
    assert "{phone}" in d_fr["corrected"] and "677000001" not in d_fr["corrected"]
    assert "{name}" in d_fr["corrected"] and "Amina" not in d_fr["corrected"]
    assert d_fr["variables"]["amount"] == "5 000 FCFA"
    assert d_fr["variables"]["phone"] == "677000001"
    assert "envoyer" in d_fr["corrected"].lower()
    assert "t5-spell-fr" in d_fr["engine"]

    r_en = client.post("/correct", json={
        "text": "I wants to checks my balance before sending 10 000 FCFA.",
        "language": "en",
    })
    assert r_en.status_code == 200
    d_en = r_en.json()
    assert "{amount}" in d_en["corrected"] and "10 000" not in d_en["corrected"]
    assert d_en["variables"]["amount"] == "10 000 FCFA"
    assert "t5-grammar-en" in d_en["engine"]


def test_full_sentence_translation_all_models_and_phonetics():
    for lang in ("ewo", "fub", "bbj", "byv", "dua", "bas", "hau", "bum", "wes", "en"):
        r = client.post("/translate", json={
            "text": "Je veux envoyer 5 000 FCFA à Jean Mbarga au 677000001 aujourd'hui pour payer sa facture ENEO.",
            "source_language": "fr",
            "target_language": lang,
            "auto_correct": True,
        })
        assert r.status_code == 200
        d = r.json()
        assert "{amount}" in d["translated_text"] and "5 000" not in d["translated_text"]
        assert "{beneficiary}" in d["translated_text"] and "Jean Mbarga" not in d["translated_text"]
        assert "{phone}" in d["translated_text"] and "677000001" not in d["translated_text"]
        assert "ENEO" in d["translated_text"]
        assert d["variables"]["amount"] == "5 000 FCFA"
        assert d["ipa"].startswith("/")
        assert d["tts_script"]
        assert d["gsm7_strict"] is True


def test_neural_tts_wav_generation():
    for lang, sample in [("ewo", "Mbolo, lom 5000 francs"), ("fub", "Sannu, nel ceede"), ("wes", "Hello, send moni"), ("fr", "Bonjour")]:
        r = client.get("/tts", params={"text": sample, "language": lang})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("audio/wav")
        assert r.content[:4] == b"RIFF"
        assert len(r.content) > 1000
