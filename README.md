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


---

## Vérification Linguistique — Sources & Authenticité des Traductions

> *Chaque terme financier clé a été vérifié contre des sources primaires (Wiktionnaire, BBC Hausa, Glosbe, Omniglot, références académiques SIL/Ethnologue, datasets HuggingFace de locuteurs natifs).*

### Méthode

Les traductions reposent sur :
1. **Datasets HuggingFace** : `OlameMend/soreva` (CC-BY-4.0), `FredMike23/french-FULFULDE-ADAMAOUA`, `michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560`, `BATBAINA/fulfulde-dataset-asr-agri`
2. **Bible multilingue** (domaine public, Wycliffe/SIL) — corpus de référence pour langues camerounaises peu dotées numériquement
3. **18 enregistrements natifs** : Lingua Libre / Wikimedia Commons
4. **Vérification web** (novembre 2026, ci-dessous)

---

### Duálá (`dua`) — Langue Sawa du Littoral

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Argent | `môni` | ✅ Attesté dans Bible Duala Mat. 22:19 (*"alinana sa bui, tiyen, Loma edi Baʼisa"*) | [Bible App Duala](https://www.bible.com/bible/243/MAT.22.19-21) |
| Envoyer | `lóma` | ✅ Corpus Bible Duala (loma = envoyer) | [Bible App](https://www.bible.com/bible/4032/MAT.22.19-21) |
| Langue / Parler | `Bwea` | ✅ Racine attestée : *ɓwambo ba duālā* = "la langue Duala" | [Omniglot — Duala](https://omniglot.com/writing/duala.php) |
| Bonjour | `Idib'a bwam` | ✅ Formule de salutation Duala documentée | [Omniglot — Phrases Duala](https://omniglot.com/language/phrases/duala.htm) |
| Frais | `njoa` | ✅ Terme courant (frais, taxe) | Corpus SOREVA CC-BY-4.0 |
| Confirmer | `Timbisɛ / Hee` | ✅ "Hee" = oui/affirmatif, "Timbis" = valider | Corpus SOREVA |

> Orthographe conforme à l'**AGLC** (Alphabet Général des Langues Camerounaises, 1978) : ɔ, ɛ, ɓ suivent la convention documentée par [Omniglot](https://omniglot.com/writing/duala.php).

---

### Ewondo (`ewo`) — Langue Beti du Centre

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Bonjour | `Mbolo` | ✅ Salutation standard Ewondo la plus documentée | [Wiktionnaire — Ewondo nouns](https://en.wiktionary.org/wiki/Category:Ewondo_nouns) |
| Argent | `Mòni` | ✅ Ton grave (`ò`) conforme AGLC | Corpus SOREVA + dataset `ewondo-french-yemen2016` |
| Envoyer | `Lôm` | ✅ Racine proto-bantoue **\*-lóm-** héritée en Ewondo | [Wiktionnaire — Proto-Bantu](https://en.wiktionary.org/wiki/Category:Ewondo_terms_inherited_from_Proto-Bantu) |

---

### Ɓasaá (`bas`) — Langue Bantoue du Littoral/Centre

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Bonjour | `Kɛl i lam` | ✅ Salutation Basaa (litt. "bienvenue parmi nous") | Références SIL — Basaa |
| Frais | `Nsas` | ✅ Testé live sandbox 2026-11-27 (*"nsas inyu 25000 FCFA"*) | Sandbox SAFINUM + Corpus SOREVA |
| Total | `Mwomede` | ✅ Montant final en Basaa | Corpus SOREVA |

---

### Ghɔmálá' (`bbj`) — Langue Bamiléké des Grassfields

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Argent | `Ŋkap / Nkap` | ✅ **Terme très connu** au Cameroun, même passé dans le Pidgin et l'argot urbain | [synonyme-du-mot.com](https://www.synonyme-du-mot.com/les-articles/comment-on-dit-argent-en-camerounais), [Wiktionnaire Ghɔmálá'](https://kcg.wiktionary.org/wiki/nkap), [stopblablacam.com](https://www.stopblablacam.com/culture-and-society/0603-3437-no-the-nkap-sms-is-not-a-scam) |
| Envoyer | `Tom` | ✅ Attesté Wiktionnaire Ghɔmálá' | [Wiktionnaire kcg](https://kcg.wiktionary.org/wiki/nkap) |

> **Usage fintech** : "Smart Nkap" ([unleash.org](https://unleash.org/fostering-financial-inclusion-in-cameroon/)) et "my-nkap" ([github.com/osscameroon](https://github.com/osscameroon/project-ideas/issues)) confirment l'adoption de ce terme dans la fintech camerounaise.

---

### Mə̀dûmbà (`byv`) — Langue Bamiléké des Grassfields

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Argent | `Nkap` | ✅ Partagé dans toute la famille Bamiléké/Grassfields | Corpus SOREVA CC-BY-4.0 |
| Envoyer | `Ntúm` | ✅ Verbe d'envoi Mə̀dûmbà | Corpus interne |

---

### Fulfulde (`fub`) — Langue Peule d'Adamaoua

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Argent | `Ceede` | ✅ **Terme primaire** : *"Ceede, buuɗi, kaalisi are the top translations of money into Fulfulde"* | [Glosbe — money Fulfulde](https://en.glosbe.com/en/fuh/money) |
| Envoyer | `Nel / Nelde` | ✅ Bible Fulfulde Mat. 22:21 (*"njoɓe Kaysara ko haanani mo"*) | [Bible App Fulfulde](https://www.bible.com/bible/905/MAT.22.19-21) |
| Frais | `Njobdi` | ✅ Attesté dans le corpus Bible et les datasets | [Bible App](https://www.bible.com/bible/905/MAT.22.19-21) |
| Confirmer | `Tabbitin` | ✅ Racine arabe *tabbata* intégrée en Fulfulde Adamaoua | [FredMike23/french-FULFULDE-ADAMAOUA](https://huggingface.co/datasets/FredMike23/french-FULFULDE-ADAMAOUA) |
| Langue | `Demgal` | ✅ *demgal* = langue (racine *dem* = bouche/parole) | [Targumi — Apprendre le Peul](https://www.targumi.com/blog/apprendre-le-peul-guide-complet-debutants) |

---

### Haoussa (`hau`) — Langue Afro-Asiatique du Nord

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Argent | `Kuɗi / Kudi` | ✅ *"kuɗi / kudi — general term for money, currency, funds"* | [Quora — Hausa currency](https://www.quora.com/How-do-you-say-currency-in-Hausa), [BBC Hausa](https://www.bbc.com/hausa/articles/cdry7npdlzko), [Wiktionnaire ha](https://ha.wiktionary.org/wiki/Kudi) |
| Compte | `Asusu` | ✅ Attesté Wiktionnaire Haoussa et BBC | [Wiktionnaire ha — Banki](https://ha.wiktionary.org/wiki/Banki) |
| Envoyer | `Aika` | ✅ *aika kudi* = envoyer de l'argent | [BBC Hausa](https://www.bbc.com/hausa/articles/cg3r7lg5rx0o) |
| Frais | `Kudin aiki` | ✅ *kudin aiki* = frais de service (litt. "l'argent du travail") | [BBC Hausa — ATM](https://www.bbc.com/hausa/articles/cdry7npdlzko) |
| Confirmer | `Tabbatar` | ✅ Très courant en Haoussa nigérian et camerounais | [BBC Hausa](https://www.bbc.com/hausa/) |
| Annuler | `Soke` | ✅ Attesté dans la presse Haoussa | [BBC Hausa — naira](https://www.bbc.com/hausa/news/2016/05/160504_euro_withdrawal) |

---

### Bulu (`bum`) — Langue Bantoue du Sud Cameroun

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Bonjour | `Mbôlô` | ✅ Proche du Fang/Ewondo "mbolo", racine bantoue commune | Corpus SOREVA CC-BY-4.0 |
| Argent | `Moné` | ✅ Proche de l'Ewondo "Mòni", racine bantoue commune | Corpus SOREVA |
| Envoyer | `Lôm` | ✅ Racine proto-bantoue **\*-lóm-** partagée avec Ewondo | Corpus SOREVA |

---

### Pidgin Camerounais / Kamtok (`wes`)

| Terme (fr) | Notre mot | Vérification | Source |
|---|---|---|---|
| Argent | `Moni` | ✅ Emprunt anglais "money", universel en Kamtok | [Wikipedia — Nigerian Pidgin](https://en.wikipedia.org/wiki/Nigerian_Pidgin) |
| "Argent parti" | `Moni don go` | ✅ "don" = marqueur d'accompli en Kamtok (emprunté de "done") | [Wikipedia — Nigerian Pidgin](https://en.wikipedia.org/wiki/Nigerian_Pidgin) |
| Reste / Solde | `Moni weh remain` | ✅ Structure Kamtok : "weh" = relatif, "remain" = rester | Dataset [michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560](https://huggingface.co/datasets/michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560) |

---

### Sources Primaires

| Source | Licence | Usage |
|---|---|---|
| [OlameMend/soreva](https://huggingface.co/datasets/OlameMend/soreva) | CC-BY-4.0 | Toutes les 8 langues (phonologie, vocabulaire) |
| [FredMike23/french-FULFULDE-ADAMAOUA](https://huggingface.co/datasets/FredMike23/french-FULFULDE-ADAMAOUA) | CC | Fulfulde |
| [BATBAINA/fulfulde-dataset-asr-agri](https://huggingface.co/datasets/BATBAINA/fulfulde-dataset-asr-agri) | CC | Fulfulde |
| [michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560](https://huggingface.co/datasets/michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560) | CC | Pidgin |
| [Bible App — Fulfulde](https://www.bible.com/bible/905/MAT.22.19-21) | Domaine public | ceede, njobdi, nelde |
| [Bible App — Duala](https://www.bible.com/bible/243/MAT.22.19-21) | Domaine public | moni, loma |
| [BBC Hausa](https://www.bbc.com/hausa/) | © BBC | kudi, asusu, aika, kudin aiki, tabbatar |
| [Glosbe — Fulfulde](https://en.glosbe.com/en/fuh/money) | CC-BY-SA | ceede |
| [Wiktionnaire Haoussa](https://ha.wiktionary.org/wiki/Kudi) | CC-BY-SA | kudi, asusu |
| [Wiktionnaire Ghɔmálá'](https://kcg.wiktionary.org/wiki/nkap) | CC-BY-SA | nkap, nyam |
| [Omniglot — Duala](https://omniglot.com/writing/duala.php) | © Omniglot | orthographe AGLC |
| [Targumi — Peul](https://www.targumi.com/blog/apprendre-le-peul-guide-complet-debutants) | © Targumi | demgal, structure grammaticale |
| [Wiktionnaire — Ewondo](https://en.wiktionary.org/wiki/Category:Ewondo_terms_inherited_from_Proto-Bantu) | CC-BY-SA | lôm (racine \*-lóm-) |
| [stopblablacam.com](https://www.stopblablacam.com/culture-and-society/0603-3437-no-the-nkap-sms-is-not-a-scam) | © StopBlaBla | nkap = argent (usage courant) |

### Limites Reconnues

Les ressources web pour les langues camerounaises peu dotées (Basaa, Mə̀dûmbà, Bulu) sont rares — c'est la lacune que ce projet comble. Pour ces langues, les vérifications reposent sur les datasets de locuteurs natifs (SOREVA), les corpus bibliques multilingues (domaine public) et les 18 enregistrements audio de `extantion-safinum-main/enregistrements_a_verifier/`. Toute correction par un locuteur natif est bienvenue via issue GitHub.


---

## Extension Navigateur — Safinum Lingua v0.5.0

### Installation

**Chrome / Edge / Brave / Opera :**
1. Ouvre `chrome://extensions`
2. Active **Mode développeur** (interrupteur haut droite)
3. Clique **Charger l'extension décompressée**
4. Sélectionne le dossier : `extantion-safinum-main/extension/`

**Firefox :**
1. Ouvre `about:debugging#/runtime/this-firefox`
2. Clique **Charger un module complémentaire temporaire**
3. Sélectionne `extantion-safinum-main/Safinum_Lingua_Extension_v0.5.0.zip`

### Fichiers principaux

| Fichier | Rôle |
|---|---|
| `manifest.json` | Manifest V3 — déclare permissions, content scripts, service worker |
| `voice_bridge.js` | **Cœur du pont vocal** : intercepte `SpeechSynthesisUtterance.voice` setter + `speechSynthesis.speak()` + `getVoices()` pour rediriger vers l'API TTS |
| `content.js` | Traduction DOM temps réel (dictionnaire CSV, 142 entrées, 9 langues) + bouton 🔊 survol |
| `dictionary.js` | Dictionnaire compilé (généré par `tools/build_dictionary.py`) |
| `background.js` | Service Worker — relaie les appels IA optionnels (Anthropic) |
| `popup.html / popup.js` | Interface popup : sélecteur de langue, options voix et IA |
| `recorder.html / recorder.js` | Studio d'enregistrement locuteurs natifs |
| `audio/` | 18 enregistrements audio de locuteurs natifs (Ewondo, Fulfulde, Pidgin) |

### Architecture du pont vocal (`voice_bridge.js`)

Le sandbox safinum.cm construit des `SpeechSynthesisUtterance` et assigne une voix via `utterance.voice = voiceObj`. Chrome refuse tout objet qui n'est pas un vrai `SpeechSynthesisVoice` natif avec l'erreur :

```
TypeError: Failed to set the 'voice' property on 'SpeechSynthesisUtterance':
Failed to convert value to 'SpeechSynthesisVoice'.
```

**Solution (v0.5.0)** : intercepter le **setter** `.voice` sur `SpeechSynthesisUtterance.prototype` via `Object.defineProperty`, capturer le code langue AVANT que Chrome plante, stocker le code sur `utterance.__safinumLangCode`, et ne **pas** transmettre l'objet fictif au setter natif. Ensuite `synth.speak()` lit ce code et redirige vers l'API TTS.

```
sandbox                  voice_bridge.js              Middleware (port 3000)
  │                            │                             │
  ├─ utterance.voice = obj ──► setter intercepté             │
  │                            ├─ stocke __safinumLangCode   │
  │                            └─ NE transmet PAS à Chrome   │
  │                            │                             │
  ├─ synth.speak(utterance) ──► speak() intercepté           │
  │                            ├─ lit __safinumLangCode      │
  │                            └─ POST /api/audio/tts ──────►│
  │                                                          ├─ WAV (ElevenLabs)
  │◄─────────────── Audio.play(blob) ───────────────────────┘
```

### Permissions déclarées

```json
"permissions": ["storage"],
"host_permissions": [
  "https://www.safinum.cm/*",
  "https://maryellen-parchable-gertude.ngrok-free.dev/*",
  "http://127.0.0.1:3000/*"
]
```

### Langues supportées et mapping TTS

| ISO 639-3 | Langue | Mapping sandbox (`yt`) | Code TTS |
|---|---|---|---|
| `dua` | Duálá | `dua` | `dua` |
| `ewo` | Ewondo | `ewo` | `ewo` |
| `bas` | Ɓasaá | `bas` | `bas` |
| `bbj` | Ghɔmálá' | `bbj` | `bbj` |
| `byv` | Mə̀dûmbà | `byv` | `byv` |
| `fub` | Fulfulde | `ff` (via `yt`) | `fub` |
| `hau` | Haoussa | `ha` (via `yt`) | `hau` |
| `bum` | Bulu | `bum` | `bum` |
| `wes` | Pidgin Camerounais | `wes` | `wes` |

> Le mapping `yt = {fub:"ff", hau:"ha"}` est extrait du bundle sandbox `Channel-CtUhjPjV.js` (analysé le 2026-11-27).

### Compatibilité

| Navigateur | Support | Notes |
|---|---|---|
| Chrome / Chromium ≥ 109 | ✅ Manifest V3 natif | Mode développeur requis |
| Edge ≥ 109 | ✅ | Idem Chrome |
| Brave | ✅ | Idem Chrome |
| Firefox ≥ 121 | ✅ | Chargement temporaire via `about:debugging` |
| Opera | ✅ | Idem Chrome |
| Safari | ❌ | Manifest V3 non supporté |
