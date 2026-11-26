# Safinum Lingua — Infrastructure Linguistique Universelle (Équipe Dev space ICT)

Solution complète de l'équipe **Dev space ICT** pour le **SAFINUM Innovate Challenge 2026 — Challenge Final**.

> *« Le challenge ne consiste pas simplement à traduire les services financiers. Il s'agit de construire l'infrastructure linguistique qui rend les services financiers accessibles partout. »*

## Architecture du Dépôt

| Dossier / Fichier | Rôle | Port |
|---|---|---|
| [`safinum-middleware/`](safinum-middleware/) | **Middleware REST principal (`POST /middleware`)** : USSD conversationnel (GSM-7 `<= 182` septets, 13 intentions, confirmation 2 tours `X-Trace-Id`) + Mobile & Web (`type: "ui_translation"`, 89 clés officielles, `{placeholders}` intacts, `max_chars`) + Phonétique IPA / TTS `fr-FR` / `MMS-TTS` + Dashboard Live (`/`). | `3000` |
| [`traduction_service_google/`](traduction_service_google/) | **Projet Traduction via Modèles IA (façon Google Traduction Pro)** : inspection & correction grammaticale/orthographique de **phrases entières** (`T5` FR & EN) + traduction neuronale hors-ligne (`flagship-ai/cameroon-int8` CTranslate2 + `OPUS-MT-Bantu/Mul`) + protection financière + IPA & Audio WAV. | `3001` |
| [`traduction_mot_a_mot/`](traduction_mot_a_mot/) | **Projet Traduction Lexicale Mot-à-Mot** : traduction mot-par-mot transparente avec alignement token-par-token, protection stricte des montants/téléphones/références, phonétique IPA/TTS et conformité GSM-7. | `3002` |
| [`extantion-safinum-main/`](extantion-safinum-main/) | **Extension Navigateur Manifest V3 (`Safinum Lingua v0.3.0`)** + corpus CSV (`142` entrées) + 18 enregistrements audio de locuteurs natifs (`Lingua Libre` / `Wikimedia Commons`). | — |
| [`models/`](models/) | **Modèles IA locaux téléchargés hors-ligne** (via `scripts/download_models.py` : `cameroon-int8`, `OPUS-MT`, `T5`, `MMS-TTS`, `ewondo-french-yemen2016`, `ewondo-tts-speecht5`) + [`manifest.json`](models/manifest.json). | — |
| [`datasets/`](datasets/) | **Datasets parallèles et lexicaux** (`OlameMend/soreva`, `FredMike23/french-FULFULDE-ADAMAOUA`, `BATBAINA/fulfulde-dataset-asr-agri`, `michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560`) compilés dans `safinum-middleware/app/data/cameroon_corpus_extract.json`. | — |
| [`LIVRABLES_FINALE_SAFINUM_2026/`](LIVRABLES_FINALE_SAFINUM_2026/) | **Dossier complet des 8 livrables attendus (§11)** : PDFs, Markdowns, schémas PNG/SVG, OpenAPI JSON, traces des 10 scénarios, présentation `.pptx` et captures. | — |
| [`docs_reference/`](docs_reference/) | Documents officiels du challenge, références phonologiques Ghɔmálá' et corpus candidats. | — |

## Langues prises en charge (9 langues)
- **8 langues officielles du sandbox (ISO 639-3)** : **Duálá (`dua`)**, **Ewondo (`ewo`)**, **Ɓasaá (`bas`)**, **Ghɔmálá (`bbj`)**, **Mə̀dûmbà (`byv`)**, **Fulfulde (`fub`)**, **Français (`fr`)**, **English (`en`)**.
- **+ Pidgin camerounais (`wes` / Kamtok)** avec **détection automatique** lorsque `language=null`.

## Installation & Lancement Rapide

```bash
# 1. Créer l'environnement Python 3.12 et installer les dépendances
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python --index-url https://download.pytorch.org/whl/cpu torch
uv pip install --python .venv/bin/python -r requirements.txt

# 2. Télécharger et quantifier les modèles IA locaux (traduction, correction T5, MMS-TTS)
.venv/bin/python scripts/download_models.py

# 3. Configurer les variables d'environnement
cp .env.example .env
# Renseignez SAFINUM_TEAM_KEY=sbx_... dans .env

# 4. Exécuter toute la suite de tests automatisés
(cd safinum-middleware && ../.venv/bin/pytest -v)
(cd traduction_mot_a_mot && ../.venv/bin/pytest -v)
(cd traduction_service_google && ../.venv/bin/pytest -v)

# 5. Démarrer les 3 services (ports 3000, 3001, 3002)
./start_all.sh
```

## Connexion au Sandbox Officiel SAFINUM (`https://www.safinum.cm/sandbox/docs`)

```bash
# Exposer le middleware sur une URL publique HTTPS
ngrok http 3000   # ou: cloudflared tunnel --url http://localhost:3000

# Enregistrer la même URL /middleware pour les 3 canaux actifs
for ch in ussd mobile web; do
  curl -s -X POST "https://www.safinum.cm/api/v1/sandbox/endpoint" \
    -H "X-Team-Key: sbx_VOTRE_CLE" \
    -H "Content-Type: application/json" \
    -d "{\"channel\":\"$ch\",\"url\":\"https://VOTRE-URL/middleware\"}"
done
```

## Régénération des Livrables & Visuels

```bash
.venv/bin/python safinum-middleware/generate_pptx.py
.venv/bin/python scripts/build_deliverables.py
```
