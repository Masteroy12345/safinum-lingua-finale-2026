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
        "text": "bonjour envoyer 5 000 FCFA à 677000001",
        "target_language": "dua",
    })
    assert r.status_code == 200
    d = r.json()
    assert "5 000 FCFA" in d["translated"]
    assert "677000001" in d["translated"]
    assert "idib'a bwam" in d["translated"].lower()
    assert any(a["status"] == "protected" for a in d["alignments"])
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
    assert "10 000 FCFA" in d_fub["translated"]
