# 7. Documentation Technique & Spécifications API

Les spécifications OpenAPI 3.1 complètes et auto-générées des trois services sont fournies dans ce dossier (`openapi_middleware.json`, `openapi_service_google.json`, `openapi_mot_a_mot.json`).

## A. Middleware Universel (`safinum-middleware`, Port 3000)

| Endpoint | Méthode | Rôle |
|---|---|---|
| `/middleware` | `POST` | Endpoint unique Gateway : USSD conversationnel (`GatewayRequest` → `GatewayResponse`) & Mobile/Web (`UITranslationRequest` → `UITranslationResponse`). |
| `/health` | `GET` | État de santé, langues (`9`) et contrats supportés. |
| `/api/diagnostics` | `GET` | Flux temps réel des traces (`trace_id`, canal, langue, intention, septets GSM-7, latence). |
| `/api/grammar` | `GET` | Règles grammaticales, pronoms et temps/aspects des langues camerounaises. |
| `/api/phonetics` | `POST` | Retourne `web_phonetic`, `ipa`, `tts_script` et `tts_voice_lang`. |
| `/api/translate` | `POST` | Traduction avec protection des montants/numéros + sortie phonétique. |
| `/api/audio/tts` | `GET`/`POST` | Synthèse audio WAV locale (Meta MMS-TTS) ou métadonnées phonétiques de repli. |
| `/` | `GET` | Tableau de bord Diagnostics Live HTML. |

## B. Service IA Traduction & Correction (`traduction_service_google`, Port 3001)

| Endpoint | Méthode | Rôle |
|---|---|---|
| `/correct` | `POST` | Corrige l'orthographe et la grammaire d'une phrase entière (T5 FR/EN) en protégeant montants, numéros et références. |
| `/translate` | `POST` | Pipeline complet : détection langue + correction T5 + traduction neuronale locale (`cameroon-int8` / `OPUS-MT`) + phonétique + GSM-7. |
| `/tts` | `GET`/`POST` | Audio WAV neural local (`MMS-TTS`). |
| `/` | `GET` | Interface Web complète façon Google Traduction Pro. |

## C. Service Lexical Mot-à-Mot (`traduction_mot_a_mot`, Port 3002)

| Endpoint | Méthode | Rôle |
|---|---|---|
| `/translate` | `POST` | Traduction mot-à-mot transparente avec tableau d'alignement token-par-token, protection financière, IPA et GSM-7. |
| `/glossary` | `GET` | Expose le lexique complet vérifié dans les 9 langues. |
| `/tts` | `GET`/`POST` | Audio WAV neural local (`MMS-TTS`). |
| `/` | `GET` | Interface Web interactive Mot-à-Mot. |
