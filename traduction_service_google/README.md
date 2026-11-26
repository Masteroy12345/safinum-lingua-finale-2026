# Sous-dossier 2 : Service IA de Traduction & Correction de Phrases (`traduction_service_google/`)

Ce module implémente l'approche **service neuronal complet** (façon Google Traduction Pro) avec **correction automatique de phrases entières** :
1. **Correction de phrases entières (`sentence_corrector.py`)** : utilise `fdemelo/t5-base-spell-correction-fr` (FR) et `vennify/t5-base-grammar-correction` (EN) téléchargés en local (`models/t5-spell-fr`, `models/t5-grammar-en`) après masquage sentinelle des entités financières.
2. **Traduction neuronale hors-ligne (`local_nmt.py`)** :
   - `flagship-ai/cameroon-int8` (CTranslate2 int8) pour `fr` ↔ `ewo`, `fub`, `bbj`, `byv`, `en`
   - `Helsinki-NLP/opus-mt-tc-bible-big-...-bnt` & `-mul` pour `dua`, `bas`, `wes` (`>>pcm<<`) + sens retour
   - Pivot automatique via le français entre toutes les paires + garde-fous terminologiques financiers SAFINUM.
3. **Phonétique & Audio** : IPA, version Web vocale adaptée pour `fr-FR`, script TTS, et synthèse WAV locale (`MMS-TTS`).

## Configuration & Lancement
```bash
cp .env.example .env
../.venv/bin/uvicorn app:app --host 0.0.0.0 --port 3001
```
Ou via `./start.sh` (Linux/macOS) ou `start.bat` (Windows).
- Interface Web : `http://localhost:3001/`
- `POST /correct` : correction d'une phrase entière sans perte des montants/numéros
- `POST /translate` : correction + traduction complète + IPA + TTS + GSM-7
- `GET/POST /tts` : synthèse audio WAV locale
