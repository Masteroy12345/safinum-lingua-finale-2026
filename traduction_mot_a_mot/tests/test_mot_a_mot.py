"""Tests du sous-projet Traduction Mot-à-Mot."""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_mot_a_mot_health_and_glossary():
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"

    g = client.get("/glossary")
    assert g.status_code == 200
    assert "dua" in g.json()["languages"]


def test_mot_a_mot_translation_and_protection():
    r = client.post("/translate", json={
        "text": "bonjour Amina envoyer 5 000 FCFA à Jean Mbarga au 677000001",
        "target_language": "dua",
    })
    assert r.status_code == 200
    d = r.json()
    assert "{name}" in d["translated"] and "Amina" not in d["translated"]
    assert "{amount}" in d["translated"] and "5 000" not in d["translated"]
    assert "{beneficiary}" in d["translated"] and "Jean Mbarga" not in d["translated"]
    assert "{phone}" in d["translated"] and "677000001" not in d["translated"]
    assert "idib'a bwam" in d["translated"].lower()
    assert any(a["status"] == "variable" for a in d["alignments"])
    assert d["variables"]["amount"] == "5 000 FCFA"
    assert d["gsm7_strict"] is True
    assert d["ipa"].startswith("/")

    r_fub = client.post("/translate", json={
        "text": "aide contrat 10 000 FCFA",
        "target_language": "fub",
    })
    assert r_fub.status_code == 200
    d_fub = r_fub.json()
    assert "ballal" in d_fub["translated"]
    assert "alkawal" in d_fub["translated"]
    assert "{amount}" in d_fub["translated"] and "10 000" not in d_fub["translated"]
