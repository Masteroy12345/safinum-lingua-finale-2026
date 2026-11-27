# ARCHITECTURE — Safinum Lingua
## Infrastructure Linguistique Universelle · Dev space ICT · SAFINUM Innovate Challenge 2026

---

## 1. Vue d'ensemble

Safinum Lingua est un middleware multicanal qui s'intercale entre la passerelle Safinum et l'API bancaire simulée. Il reçoit les requêtes des simulateurs (USSD, Mobile, Web, SMS, ATM, IVR), les comprend dans 9 langues camerounaises, appelle l'API bancaire en son nom, et retourne une réponse traduite dans la langue de l'utilisateur.

```
Simulateur (navigateur)
       │  POST /api/v1/channel/{canal}
       ▼
 Passerelle Safinum ──── X-Trace-Id ────┐
       │  POST {url_equipe}/middleware   │
       ▼                                │
  SAFINUM LINGUA                        │
  (port 3000, Python/FastAPI)           │
       │  X-Team-Key + X-Trace-Id       │
       ▼                                ▼
  API bancaire simulée ────────► Journal du jury
       │
       ▼
  Service TTS Vercel
  (safinum-tts-v2.vercel.app)
       │
       ▼
  ElevenLabs eleven_multilingual_v2
```

---

## 2. Composants

### 2.1 Middleware principal · `safinum-middleware/`

| Module | Rôle | Taille |
|--------|------|--------|
| `app/main.py` | Point d'entrée FastAPI, dispatch par canal | 2 027 lignes |
| `app/languages.py` | Glossaires, gabarits, traduction, détection | 1 072 lignes |
| `app/ui_translator.py` | Traduction d'écrans Mobile/Web/ATM | 1 369 lignes |
| `app/nlu.py` | Compréhension des intentions utilisateur | 407 lignes |
| `app/phonetics.py` | Phonétique AGLC, TTS ElevenLabs, SOREVA | 657 lignes |
| `app/bank_client.py` | Client async API bancaire, X-Trace-Id | 124 lignes |
| `app/ivr_handler.py` | Transcription audio, Gemini 3.1 Flash Lite | 155 lignes |
| `app/session_store.py` | État de session par numéro de téléphone | 56 lignes |
| `app/gsm7.py` | Contraintes GSM-7, comptage septets | 160 lignes |
| `app/models.py` | Modèles Pydantic (contrat passerelle) | 108 lignes |
| `app/config.py` | Variables d'environnement | 30 lignes |

### 2.2 Service TTS · `safinum-tts-v2/`

Fonction Vercel serverless Node.js déployée en production sur `https://safinum-tts-v2.vercel.app/api/tts`.  
Reçoit `{text, language}`, appelle ElevenLabs, retourne MP3.

### 2.3 Extension navigateur · `extantion-safinum-main/`

Extension Chrome v1.0.0 qui intercepte `speechSynthesis.speak()` sur safinum.cm et redirige vers le service TTS Vercel pour une lecture dans la vraie voix de la langue.

### 2.4 Services annexes (ports 3001, 3002)

- **Port 3001** — Service de traduction par phrase (pivot FR → langue cible)
- **Port 3002** — Service mot-à-mot avec glossaire AGLC

---

## 3. Architecture interne du middleware

### 3.1 Flux général par requête

```
POST /middleware
      │
      ├─ [1] Lecture headers : X-Trace-Id, Content-Type
      │
      ├─ [2] Dispatch par canal
      │       ├── channel == "ivr" && input.type == "audio"
      │       │       └─► ivr_handler.py : Gemini 3.1 Flash Lite STT
      │       │                           → texte transcrit → patch payload (dtmf)
      │       ├── type == "ui_translation"  (mobile, web, atm)
      │       │       └─► ui_translator.py : traduction clé-par-clé avec max_chars
      │       └── channel == "sms" sans session_id
      │               └─► patch contraintes gsm7_ucs2 / 160 chars
      │
      ├─ [3] NLU (nlu.py)
      │       ├── Extraction déterministe : regex + glossaire (< 5 ms)
      │       └── Repli neuronal : CTranslate2 OPUS-MT local si aucun mot reconnu
      │
      ├─ [4] Résolution langue
      │       ├── normalize_language(req.language)
      │       ├── ou detect_language(text) si language == null
      │       └── fallback : langue de session, puis "fr"
      │
      ├─ [5] Appels API bancaire (bank_client.py)
      │       ├── BALANCE_INQUIRY  → GET /accounts/{phone}
      │       ├── TRANSFER         → GET /fees, POST /transactions
      │       ├── CONFIRM          → POST /transactions/{id}/confirm
      │       ├── CORRECTION       → POST /transactions/{id}/update
      │       ├── FEE_INQUIRY      → GET /fees
      │       ├── TRANSACTION_HISTORY → GET /accounts/{phone}/transactions
      │       └── TERM_EXPLANATION → aucun appel bancaire
      │
      ├─ [6] Construction de la réponse
      │       ├── get_text(lang, clé, canal)   ← gabarits languages.py
      │       ├── fmt_amount(montant)           ← formatage local
      │       ├── fit_channel_constraints(texte, canal) ← gsm7.py (USSD 182 septets)
      │       └── build_audio_payload(texte, lang)      ← phonetics.py (IPA + TTS)
      │
      └─ [7] Réponse JSON passerelle
              {
                "response":        { "text", "end_session", "options" },
                "interpretation":  { "intent", "parameters", "language" },
                "transaction":     { "id", "status" }
              }
```

### 3.2 Gestion des sessions

Chaque numéro de téléphone a une session en mémoire (`session_store.py`) :

```python
@dataclass
class Session:
    language: str           # langue active
    pending_tx_id: str      # transaction pending en cours
    pending_op: dict        # détails de l'opération à confirmer
    awaiting_field: str     # champ attendu ("montant", "beneficiaire", ...)
    draft_op_type: str      # type d'opération en cours
    last_channel: str       # dernier canal utilisé (multicanal)
```

La clé est le numéro normalisé : `237651841190`, `+237651841190`, `651841190` → même session.  
Cela permet le parcours **multicanal** : initier sur USSD, confirmer par SMS.

---

## 4. Moteur linguistique

### 4.1 Pipeline de traduction

```
Texte FR (source)
      │
      ▼ Étape 1 : Glossaire financier exact (WORD_GLOSSARY)
      │   "solde" → "mòni wom" (ewo) — 100% fiable, < 1 ms
      │
      ▼ Étape 2 : Gabarits de phrases complètes
      │   "Votre solde est de {amount}" → "Mòni wom mà : {amount}" (ewo)
      │   Couvre les 10 scénarios officiels dans les 9 langues
      │
      ▼ Étape 3 : Corpus SOREVA (CC-BY-4.0)
      │   150 phrases parallèles vérifiées par locuteurs natifs par langue
      │
      ▼ Étape 4 : Traduction mot-à-mot + connecteurs grammaticaux
      │   Suppression des articles définis FR, inversion verbe-objet selon la langue
      │
      ▼ Étape 5 : Moteur neuronal OPUS-MT local (CTranslate2)
          Utilisé uniquement pour les phrases hors glossaire
          Modèle : Helsinki-NLP/opus-mt-fr-xx quantifié int8
```

### 4.2 Orthographe — Alphabet AGLC

Toutes les langues utilisent l'**Alphabet Général des Langues Camerounaises (AGLC)** standardisé en 1978.

| Symbole | Prononciation | Exemple |
|---------|--------------|---------|
| `ɛ` | è ouvert | Ɓasaá |
| `ɔ` | o ouvert | Ewondo → "Mòni" |
| `ŋ` | nasale vélaire (ng) | Ghɔmálá' → "ŋkap" |
| `ə` | e neutre | Mə̀dûmbà |
| `ɓ ɗ ƙ ƴ` | consonnes implosives Haoussa | Ɓasaá, Fulfulde |

Stockage : **Unicode NFC**. Affichage USSD : translittération GSM-7 automatique (`ɛ→e`, `ŋ→ng`).

### 4.3 Détection automatique de langue (`language == null`)

Quand la passerelle envoie `"language": null`, `detect_language()` analyse le texte :

```
Tokens du texte utilisateur
      │
      ├── Mots Ewondo reconnus ?    → "ewo"
      ├── Mots Duálá reconnus ?     → "dua"
      ├── Mots Haoussa reconnus ?   → "hau"
      ├── Mots Pidgin reconnus ?    → "wes"
      ├── Mots français uniquement? → "fr"
      └── Rien reconnu              → "fr" (fallback)
```

---

## 5. Pipeline audio (TTS)

```
Texte traduit en langue nationale
      │
      ▼ [1] _sanitize_for_tts()
      │   Supprime : numéros de téléphone → [numéro]
      │              IDs transaction      → [réf]
      │   Raison : données personnelles ne quittent jamais le middleware
      │
      ▼ [2] to_tts_script(text, lang)   ← phonetics.py
      │   Convertit symboles AGLC en séquences lisibles par ElevenLabs :
      │   ɛ→è, ŋ→ng, ɔ→o, tons marqués par accents français
      │   Applique tonalité SOREVA (_prepare_elevenlabs_native_text)
      │
      ▼ [3] Service TTS Vercel  (safinum-tts-v2.vercel.app/api/tts)
      │   POST { text: script_phonétique, language: "ewo" }
      │   Rate limit : 20 req/min par IP
      │   Langues autorisées : 9 codes camerounais + fr + en
      │   Max texte : 1 000 chars
      │
      ▼ [4] ElevenLabs eleven_multilingual_v2
      │   Voice : Brian (nPczCjzI2devNBz1zQrb)
      │   Paramètres : stability=0.6, similarity_boost=0.8, style=0.3
      │
      ▼ [5] MP3 → cache navigateur (Map en mémoire, TTL session)
            Lecture audio dans le navigateur via voice_bridge.js
```

### 5.1 Sécurité du service TTS Vercel

| Couche | Mécanisme |
|--------|-----------|
| Données personnelles | Anonymisées par `_sanitize_for_tts()` avant tout envoi |
| Clé ElevenLabs | Variable secrète Vercel, jamais dans le code |
| Rate limit | 20 req/min par IP (en-tête X-RateLimit) |
| CORS | Restreint à `safinum.cm` et `localhost` en dev |
| Validation | Liste blanche de langues, longueur max 1 000 chars, rejet HTML/URLs |
| Headers sécurité | `X-Content-Type-Options`, `X-Frame-Options`, `CSP: default-src 'none'` |

---

## 6. Intégration à l'API bancaire simulée

### 6.1 Authentification

Chaque appel bancaire transporte deux en-têtes obligatoires :

```http
X-Team-Key: sbx_P52-4BZ           ← clé d'équipe, unique et secrète
X-Trace-Id: {trace_id reçu}       ← copié de la requête passerelle
Accept: application/json
```

Le `X-Trace-Id` reçu de la passerelle est **recopié à l'identique** sur chaque appel bancaire. C'est lui qui relie l'intention déclarée aux appels effectués dans le journal du jury.

### 6.2 Carte des appels par intention

| Intention | Appels bancaires | Ordre |
|-----------|-----------------|-------|
| `BALANCE_INQUIRY` | `GET /accounts/{phone}` | 1 |
| `TRANSFER` | `GET /fees?type=transfer&amount=X` puis `POST /transactions` | 2 |
| `CONFIRM` | `POST /transactions/{id}/confirm` | 1 (X-Trace-Id **différent** du tour d'initiation) |
| `CORRECTION` | `POST /transactions/{id}/update` | 1 |
| `CANCEL` | `POST /transactions/{id}/cancel` | 1 |
| `FEE_INQUIRY` | `GET /fees?type=transfer&amount=X` | 1 |
| `TRANSACTION_HISTORY` | `GET /accounts/{phone}/transactions?limit=10` | 1 |
| `AIRTIME_PURCHASE` | `GET /fees?type=airtime&amount=X` puis `POST /transactions` | 2 |
| `BILL_PAYMENT` | `GET /billers` puis `POST /transactions` | 2 |
| `CLARIFICATION_NEEDED` | **Aucun** | — |
| `TERM_EXPLANATION` | **Aucun** | — |
| `LANGUAGE_SWITCH` | **Aucun** | — |

### 6.3 Règle des deux tours (transfert)

```
Tour N — initiation
  Passerelle → middleware (X-Trace-Id: TID-001)
  middleware → GET /fees              (X-Trace-Id: TID-001)
  middleware → POST /transactions     (X-Trace-Id: TID-001)   ← pending, rien débité
  middleware → passerelle : relecture + "1.Confirm 0.Annuler"

Tour N+1 — confirmation
  Passerelle → middleware (X-Trace-Id: TID-002)   ← NOUVEAU trace_id
  middleware → POST /transactions/{id}/confirm     (X-Trace-Id: TID-002)
  middleware → passerelle : succès
```

> **Règle absolue :** confirmer avec le même `X-Trace-Id` que l'initiation → opération marquée ÉCHEC. Le middleware stocke `pending_tx_id` en session et refuse le confirm au même tour.

### 6.4 Gestion des erreurs API

```python
# bank_client.py — tous les codes d'erreur sont catchés
except BankApiError as e:
    if e.code == "INSUFFICIENT_FUNDS":
        → afficher solde + options dans la langue (jamais le code brut)
    elif e.code == "UNKNOWN_BENEFICIARY":
        → si e.candidates : demander précision (homonymes)
        → sinon : signaler bénéficiaire inconnu
    elif e.code == "LIMIT_EXCEEDED":
        → signaler plafond (500 000 FCFA max)
    elif e.code == "TX_NOT_PENDING":
        → transaction déjà exécutée ou annulée
    elif e.code == "CONFIG_LOCKED":
        → équipe en évaluation, configuration gelée
```

### 6.5 Timeout et budget temporel

| Canal | Budget total | Timeout HTTP client |
|-------|-------------|---------------------|
| USSD | 3 000 ms | 2 000 ms |
| Mobile/Web | 10 000 ms | 2 000 ms |
| SMS | 10 000 ms | 2 000 ms |
| ATM | 10 000 ms | 2 000 ms |
| IVR | 8 000 ms | 20 000 ms (Gemini STT) |

Le `request_timeout_s = 2.0` dans `config.py` garantit que les appels bancaires ne consomment pas tout le budget. L'IVR déduit le temps de transcription Gemini du budget restant.

---

## 7. Contraintes par canal

| Canal | Alphabet | Max | Mode | Particularité |
|-------|---------|-----|------|---------------|
| USSD | GSM-7 | 182 septets | menu | ɛ ɔ ŋ → translittération, sinon UCS-2 (70 chars) |
| Mobile | UTF-8 | par clé | ui_translation | Placeholders `{amount}` intacts |
| Web | UTF-8 | par clé | ui_translation | Identique Mobile |
| SMS | GSM-7/UCS-2 | 160 chars | async | Sans session, max 3 segments |
| ATM | UTF-8 | 18 chars (touches) | ui_translation | Écran 40 colonnes |
| IVR | UTF-8 | 400 chars | voice | Réponse texte lue par la synthèse sandbox |

---

## 8. Tunnel et déploiement

```
Machine locale
  ├── safinum-middleware/   uvicorn :3000
  ├── traduction_service/  uvicorn :3001
  └── traduction_mot_a_mot/ uvicorn :3002

ngrok (tunnel stable)
  └── https://maryellen-parchable-gertude.ngrok-free.dev → localhost:3000

Vercel (permanent)
  └── https://safinum-tts-v2.vercel.app/api/tts   ← TTS ElevenLabs
```

### Enregistrement des endpoints (automatique au démarrage)

`start.sh` :
1. Détecte si ngrok tourne → récupère l'URL publique via `localhost:4040/api/tunnels`
2. Enregistre les 6 canaux sur `POST /api/v1/sandbox/endpoint` avec l'URL ngrok
3. Lance uvicorn

```bash
bash safinum-middleware/start.sh
# → Détection ngrok : https://maryellen-parchable-gertude.ngrok-free.dev
# → Enregistrement ussd, mobile, web, sms, atm, ivr ✓
# → uvicorn app.main:app --host 0.0.0.0 --port 3000
```

---

## 9. Sécurité et confidentialité

| Principe | Implémentation |
|----------|---------------|
| Données personnelles hors cloud | `_sanitize_for_tts()` supprime numéros et IDs avant ElevenLabs |
| Clés secrètes | `.env` local (non commité), variables Vercel pour le TTS |
| Isolation des équipes | X-Team-Key sur chaque appel bancaire ; l'API bancaire renvoie 401 si absente |
| Pas de stockage audio | Cache WAV en mémoire uniquement, jamais sur disque ni dans les logs |
| Intégrité du code | Pas de dépendance à des services tiers non vérifiés ; toutes les clés en variables d'env |
| CORS TTS | Restreint à `safinum.cm` |

---

## 10. Dépendances principales

```
Python 3.12
├── fastapi 0.110          API REST async
├── uvicorn 0.29           Serveur ASGI
├── httpx 0.27             Client HTTP async (appels bancaires, Gemini, ElevenLabs)
├── pydantic v2            Validation des modèles passerelle
├── python-dotenv          Chargement .env
└── ctranslate2 (optionnel) Moteur neuronal OPUS-MT quantifié int8

Node.js 20 (Vercel)
└── Service TTS sans dépendance NPM (fetch natif Node.js 20)

Chrome Extension
└── Manifest V3, content script + service worker
```

---

## 11. Structure du dépôt

```
SAFINUM_FINALE/
├── ARCHITECTURE.md          ← ce document
├── LANGUES.md               ← sources de traduction, phonétique, audio
├── README.md                ← guide de démarrage rapide
├── scenarios/               ← 108 fiches de test par interface/langue
├── safinum-middleware/      ← middleware Python/FastAPI (port 3000)
│   ├── app/
│   │   ├── main.py          dispatch, routes
│   │   ├── languages.py     traduction, glossaires
│   │   ├── ui_translator.py mobile/web/atm
│   │   ├── nlu.py           compréhension d'intention
│   │   ├── phonetics.py     AGLC, SOREVA, TTS
│   │   ├── bank_client.py   API bancaire
│   │   ├── ivr_handler.py   Gemini STT
│   │   ├── session_store.py état par numéro
│   │   └── gsm7.py          contraintes USSD
│   └── start.sh             démarrage + enregistrement ngrok
├── safinum-tts-v2/          ← service TTS Vercel (Node.js)
├── extantion-safinum-main/  ← extension Chrome v1.0.0
│   └── extension/
│       ├── voice_bridge.js  interception speechSynthesis
│       ├── content.js       injection de voix
│       └── manifest.json    Manifest V3
├── datasets/                ← corpus SOREVA et glossaires
├── models/                  ← modèles OPUS-MT CTranslate2 (optionnel)
└── scenarios/               ← fiches de test
```
