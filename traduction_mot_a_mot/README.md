# Sous-dossier 1 : Traduction Mot-à-Mot (`traduction_mot_a_mot/`)

Ce module isole l'approche **lexicale mot-à-mot** :
- Chaque mot financier reconnu dans le lexique vérifié (`WORD_GLOSSARY` + connecteurs : `fr`, `en`, `wes`, `fub`, `ewo`, `dua`, `bas`, `bbj`, `byv`) est traduit individuellement avec un tableau d'alignement token-par-token.
- Les montants (`FCFA` / `XAF`), numéros de téléphone (`+237` / `6XXXXXXXX`) et références (`TRX-...`, `SAF-...`) sont automatiquement protégés puis réinjectés à l'identique.
- Sortie enrichie : transcription phonétique IPA, script audio TTS optimisé (`fr-FR`/`en-US`), audio neural WAV (`MMS-TTS` si disponible) et contrôle GSM-7 (`<= 182 septets`).

## Configuration & Lancement
```bash
cp .env.example .env
../.venv/bin/uvicorn app:app --host 0.0.0.0 --port 3002
```
Ou via `./start.sh` (Linux/macOS) ou `start.bat` (Windows).
- Interface Web : `http://localhost:3002/`
- `GET /health` : état du service
- `GET /glossary` : liste des mots et langues
- `POST /translate` : `{"text": "bonjour envoyer 5 000 FCFA", "target_language": "dua"}`
- `GET/POST /tts` : synthèse audio WAV locale
