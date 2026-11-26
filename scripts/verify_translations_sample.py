"""Affiche un échantillon complet des corrections T5, traductions neuronales, phonétique IPA/TTS et mot-à-mot."""
import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "traduction_service_google"))
from app import app as g_app  # noqa: E402

gc = TestClient(g_app)

print("=== 1. CORRECTION PHRASE ENTIERE (T5 FR & EN) ===")
for txt, lang in [
    ("bonjor je veu envoye 5 000 FCFA a 677000001 sil vou plait", "fr"),
    ("I wants to checks my balance before sending 10 000 FCFA.", "en"),
]:
    r = gc.post("/correct", json={"text": txt, "language": lang}).json()
    print(f"[{lang}] {txt}\n  -> {r['corrected']} ({r['engine']})")

print("\n=== 2. TRADUCTION COMPLETE VIA MODELES LOCAUX ===")
sample = "Bonjour, je veux envoyer 5 000 FCFA à mon frère pour payer la facture ENEO."
for tgt in ("ewo", "fub", "bbj", "byv", "dua", "bas", "wes", "en"):
    r = gc.post("/translate", json={"text": sample, "source_language": "fr", "target_language": tgt, "auto_correct": True}).json()
    print(f"[{tgt}] ({r['engine']}) {r['translated_text']}\n     IPA: {r['ipa']}\n     TTS: {r['tts_script']}")
