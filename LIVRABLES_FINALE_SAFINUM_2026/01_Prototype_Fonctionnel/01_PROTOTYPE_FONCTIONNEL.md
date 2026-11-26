# 1. Prototype Fonctionnel — Safinum Lingua (Dev space ICT)

**Safinum Lingua** est un écosystème logiciel complet et opérationnel composé de **4 briques complémentaires** connectées sans modifier le code source bancaire :

1. **Middleware REST Universel (`safinum-middleware/`, port `3000`)** :
   - Implémente les deux contrats officiels de la passerelle Safinum (`POST /middleware`) :
     - **Contrat USSD conversationnel** (`channel="ussd"`, GSM-7 strict <= 182 septets, timeout 3 s, confirmation 2 tours).
     - **Contrat Mobile & Web (`type="ui_translation"`)** traduisant les 89 clés officielles sur les 6 écrans (`home`, `transfer`, `pay`, `review`, `receipt`, `history`) avec préservation des emplacements (`{amount}`, `{name}`, `{fee}`, `{missing}`, `{max}`) et respect strict des `max_chars`.
   - Expose également un **Dashboard Diagnostics Live (`GET /`)**, `GET /health`, `GET /api/grammar`, `POST /api/phonetics`, `POST /api/translate`, `GET/POST /api/audio/tts`.
2. **Service IA de Traduction & Correction Complète (`traduction_service_google/`, port `3001`)** :
   - Interface web façon Google Traduction Pro + API REST (`/correct`, `/translate`, `/tts`).
   - Inspecte et corrige les phrases entières via les modèles T5 locaux (`fdemelo/t5-base-spell-correction-fr`, `vennify/t5-base-grammar-correction`) après masquage sentinelle des données financières.
   - Traduit hors-ligne dans les 9 langues grâce aux modèles neuronaux téléchargés (`flagship-ai/cameroon-int8` CTranslate2 + `Helsinki-NLP/opus-mt-tc-bible-big` Bantu & Mul).
3. **Service de Traduction Lexicale Mot-à-Mot (`traduction_mot_a_mot/`, port `3002`)** :
   - Interface web + API (`/translate`, `/glossary`, `/tts`) affichant l'alignement mot-par-mot, les entités protégées, l'IPA, le script vocal TTS et les septets GSM-7.
4. **Extension Navigateur Complémentaire (`Safinum_Lingua_Extension_v0.3.0.zip`)** :
   - Extension Manifest V3 (Chrome/Edge/Brave/Opera/Firefox) injectant la traduction DOM temps réel et la lecture vocale hors-ligne sur toute banque web existante.

## Démarrage rapide (Linux & Windows)

```bash
# 1. Configurer la clé d'équipe
cp .env.example .env

# 2. Télécharger / vérifier les modèles IA locaux (déjà téléchargés dans models/)
.venv/bin/python scripts/download_models.py

# 3. Lancer tous les services (ports 3000, 3001, 3002)
./start_all.sh
```
