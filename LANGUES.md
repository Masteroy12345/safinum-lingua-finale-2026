# Safinum Lingua — Documentation des Langues, Traductions et Audio

**Équipe Dev space ICT — SAFINUM Innovate Challenge 2026**

Ce document liste toutes les langues prises en charge, explique comment les traductions ont été obtenues, et décrit la gestion de l'audio. Il répond aux critères d'évaluation : *Précision Linguistique*, *Technologie de pointe et sécurité*, *Écriture des langues et phonétique*.

---

## 1. Langues Prises en Charge (9 langues)

| ISO 639-3 | Famille | Locuteurs (Cameroun) | Canaux |
|---|---|---|---|
| `dua` | **Duálá** — Bantoue Sawa (Littoral) | ~100 000 | USSD, Mobile, Web, SMS, IVR, ATM |
| `ewo` | **Ewondo** — Bantoue Beti (Centre) | ~600 000 | USSD, Mobile, Web, SMS, IVR, ATM |
| `bas` | **Ɓasaá** — Bantoue (Littoral/Centre) | ~300 000 | USSD, Mobile, Web, SMS, IVR |
| `bbj` | **Ghɔmálá'** — Bantoïde Grassfields (Ouest) | ~500 000 | USSD, Mobile, Web, SMS, IVR |
| `byv` | **Mə̀dûmbà** — Bantoïde Grassfields (Ouest) | ~400 000 | USSD, Mobile, Web, SMS, IVR |
| `fub` | **Fulfulde Adamaoua** — Atlantique Peule (Adamaoua) | ~3 M (Afrique centrale) | USSD, Mobile, Web, SMS, IVR |
| `hau` | **Haoussa** — Afro-Asiatique (Extrême-Nord) | ~50 M (Afrique de l'Ouest) | USSD, Mobile, Web, SMS, IVR |
| `bum` | **Bulu** — Bantoue (Sud) | ~300 000 | USSD, Mobile, Web, SMS |
| `wes` | **Pidgin Camerounais (Kamtok)** — Créole anglais | ~10 M (lingua franca nationale) | USSD, Mobile, Web, SMS, IVR |
| `fr` | **Français** — pivot de traduction | — | Tous canaux |
| `en` | **Anglais** — pivot secondaire | — | Tous canaux |

> Le Français et l'Anglais servent de langues pivots pour la détection automatique et la traduction neuronale. Ils ne sont pas comptés parmi les 9 langues nationales mais sont entièrement pris en charge.

---

## 2. Orthographe — Alphabet AGLC

Toutes les langues camerounaises utilisent l'**Alphabet Général des Langues Camerounaises (AGLC)**, standardisé en 1978 par le CERDOTOLA et la DGRNE.

Caractères spéciaux normalisés en **NFC (Unicode Normalization Form C)** :

| Symbole | Prononciation | Exemple |
|---|---|---|
| `ɛ` | comme "è" (voyelle ouverte mi-antérieure) | Ɓasaá → nsas |
| `ɔ` | comme "o" ouvert | Ewondo → Mòni |
| `ŋ` | nasale vélaire (comme "ng" dans "parking") | Ghɔmálá' → ŋkap |
| `ə` | comme "e" neutre | Mə̀dûmbà → mə̀ |
| `ɓ` | occlusive bilabiale implosive | Ɓasaá |
| `ɗ` | occlusive alvéolaire implosive | Fulfulde → ɓoodi |
| `ƴ` | fricative palatale voisée | Fulfulde → ƴeewit |
| `ʔ` | coup de glotte | Ghɔmálá' → Ŋkap |
| Tons | diacritiques combinants (grave, aigu, circonflexe) | `mòni`, `lôm`, `môni` |

### Conformité de l'implémentation

- Toutes les chaînes sont normalisées en NFC avant traitement (`unicodedata.normalize("NFC", text)`)
- Le moteur phonétique `phonetics.py` applique des règles AGLC → IPA pour chaque langue
- Les tons lexicaux sont préservés dans les gabarits USSD/Mobile (aucune suppression automatique)
- La protection des diacritiques essentiels (é, è, à, ô, ê) est maintenue dans `to_web_phonetic_safe()`

---

## 3. Comment les Traductions ont été Obtenues

### 3.1 Datasets de Locuteurs Natifs (source primaire)

| Dataset | Langues | Licence | Utilisation |
|---|---|---|---|
| [OlameMend/soreva](https://huggingface.co/datasets/OlameMend/soreva) | dua, ewo, bas, bbj, byv, fub, bum | **CC-BY-4.0** | Corpus phonologique et lexical principal — 150 phrases par langue, tonalité et prosodie natives copiées dans ElevenLabs via `native_voice_bank.py` |
| [FredMike23/french-FULFULDE-ADAMAOUA](https://huggingface.co/datasets/FredMike23/french-FULFULDE-ADAMAOUA) | fub | CC | Paires FR-Fulfulde Adamaoua — ceede, nel, tabbitin, njobdi |
| [BATBAINA/fulfulde-dataset-asr-agri](https://huggingface.co/datasets/BATBAINA/fulfulde-dataset-asr-agri) | fub | CC | ASR Fulfulde — validation phonologique |
| [michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560](https://huggingface.co/datasets/michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560) | wes | CC | 560 paires anglais-Kamtok — moni, don go, pesin, wuna |

### 3.2 Corpus Bibliques Multilingues (domaine public)

Les Bibles multilingues (Wycliffe/SIL) sont le seul corpus parallèle de grande taille pour les langues camerounaises peu dotées numériquement. Utilisées uniquement pour vérifier les racines lexicales, jamais comme source unique.

| Langue | Source | Termes vérifiés |
|---|---|---|
| Duálá | [Bible App — Duala #243](https://www.bible.com/bible/243/MAT.22.19-21) | môni (argent), lóma (envoyer) |
| Fulfulde | [Bible App — Fulfulde #905](https://www.bible.com/bible/905/MAT.22.19-21) | ceede, njoɓe (njobdi), nel |

### 3.3 Sources Web Vérifiées

| Terme | Langue | Source | URL |
|---|---|---|---|
| `nkap` = argent | bbj, byv | Wiktionnaire Ghɔmálá', stopblablacam.com | [kcg.wiktionary.org](https://kcg.wiktionary.org/wiki/nkap) |
| `kudi` = argent | hau | BBC Hausa, Wiktionnaire Haoussa | [ha.wiktionary.org](https://ha.wiktionary.org/wiki/Kudi) |
| `asusu` = compte | hau | BBC Hausa, Wiktionnaire | [ha.wiktionary.org](https://ha.wiktionary.org/wiki/Banki) |
| `aika` = envoyer | hau | BBC Hausa | [bbc.com/hausa](https://www.bbc.com/hausa/) |
| `ceede` = argent | fub | Glosbe Fulfulde | [glosbe.com](https://en.glosbe.com/en/fuh/money) |
| `tabbitin` = confirmer | fub | Dataset FredMike23 + BBC Hausa | [HuggingFace](https://huggingface.co/datasets/FredMike23/french-FULFULDE-ADAMAOUA) |
| `demgal` = langue | fub | Targumi Peul | [targumi.com](https://www.targumi.com/blog/apprendre-le-peul-guide-complet-debutants) |
| `mbolo` = bonjour | ewo, bum | Wiktionnaire Ewondo | [en.wiktionary.org](https://en.wiktionary.org/wiki/Category:Ewondo_nouns) |
| `lôm` = envoyer | ewo | Proto-Bantu \*-lóm- | [en.wiktionary.org](https://en.wiktionary.org/wiki/Category:Ewondo_terms_inherited_from_Proto-Bantu) |
| `idib'a bwam` = bonjour | dua | Omniglot Duala | [omniglot.com](https://omniglot.com/language/phrases/duala.htm) |
| `moni` = argent | wes | Wikipedia Nigerian Pidgin | [en.wikipedia.org](https://en.wikipedia.org/wiki/Nigerian_Pidgin) |
| `don go` = parti | wes | Dataset MT560 | [HuggingFace MT560](https://huggingface.co/datasets/michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560) |

### 3.4 Modèles de Traduction Neuronale (hors-ligne)

| Modèle | Langues | Usage |
|---|---|---|
| `flagship-ai/cameroon-int8` (CTranslate2) | fr ↔ ewo, dua, bas, bbj, byv, fub, hau, wes | Traduction neuronale hors-ligne (service port 3001) |
| `Helsinki-NLP/opus-mt-ROMANCE-en` (OPUS-MT) | fr → en | Pivot intermédiaire |
| `google-t5/t5-small` (correction T5) | fr, en | Correction grammaticale / orthographique avant traduction |
| `facebook/mms-tts-fra` (MMS-TTS) | fr (repli vocal hors-ligne) | Synthèse vocale de secours si ElevenLabs indisponible |

> **Intégrité du code source** : aucun modèle n'est modifié ; ils sont utilisés en inférence uniquement. Les poids sont téléchargés via `scripts/download_models.py` depuis HuggingFace avec vérification du hash.

### 3.5 Enregistrements de Locuteurs Natifs

**18 enregistrements audio** de locuteurs natifs volontaires, stockés dans `extantion-safinum-main/enregistrements_a_verifier/`, indexés dans `index.csv` :

| Langue | Enregistrements | Source | Licence |
|---|---|---|---|
| Ewondo (`ewo`) | 7 fichiers | Lingua Libre / Wikimedia Commons | CC-BY-SA 4.0 |
| Fulfulde (`fub`) | 6 fichiers | Contributions volontaires | CC-BY 4.0 |
| Pidgin (`wes`) | 5 fichiers | Contributions volontaires | CC-BY 4.0 |

Ces enregistrements servent de **référence de vérification** pour valider la prononciation des termes financiers clés. Ils ne sont pas injectés directement dans la synthèse ElevenLabs — leur tonalité et prosodie sont extraites par `native_voice_bank.py` et utilisées comme paramètres prosodiques.

---

## 4. Gestion de l'Audio

### 4.1 Architecture

```
Texte traduit (langue nationale)
        │
        ▼
phonetics.py : to_tts_script(text, lang)
        │  remplace ɛ→è, ŋ→ng, ɓ→b, ə→e, ʉ→ou
        │  développe les montants en mots (15000 → quinze mille)
        │  préserve noms propres, références TRX-, numéros
        │
        ▼
native_voice_bank.py : apply_native_tonality(text, lang)
        │  injecte les accents du corpus SOREVA (CC-BY-4.0)
        │
        ▼
ElevenLabs API (eleven_multilingual_v2, voix Brian)
        │  language_code = "fr" (sauf Pidgin → "en")
        │  stability=0.55, similarity_boost=0.78, style=0.12
        │
        ▼
_ensure_male_timbre() : garantit une voix 100% masculine (~120 Hz)
        │  si f0 > 148 Hz → décalage vers 122 Hz via ffmpeg asetrate
        │
        ▼
WAV 24 kHz PCM 16-bit → retourné au navigateur
        │
        ▼ (si ElevenLabs indisponible)
MMS-TTS local (mms-tts-fra, Facebook Research)
        WAV 16 kHz, même timbre masculin
```

### 4.2 Sécurité et Confidentialité de l'Audio

- **Aucune donnée client dans l'audio** : les montants, noms de bénéficiaires et numéros de téléphone sont lus en français dans le flux vocal, mais ne sont jamais envoyés à une API tierce en clair sans anonymisation.
- **Clé ElevenLabs** : stockée dans `.env` (hors Git via `.gitignore`), jamais dans le code source. Accessible uniquement côté serveur via `app/config.py`.
- **Cache LRU** : 96 entrées maximum (`_ELEVENLABS_WAV_CACHE`, `OrderedDict`). Les WAV sont stockés en mémoire, jamais sur disque.
- **Validation des chemins audio natifs** : `serve_native_audio()` valide que le chemin résolu reste sous `_NATIVE_AUDIO_DIR` pour éviter les path traversal (`.." bloqué`).

### 4.3 Phonétique par Langue

| Langue | Règles appliquées | Exemple |
|---|---|---|
| Ewondo | ɛ→è, ŋ→ng, ə→e, groupe Mb→Meb | `mòni` → `moni` (lu correctement en fr-FR) |
| Duálá | ɔ→o, ɓ→b, ʼ→ (coup de glotte supprimé) | `timbisɛ` → `timbise` |
| Ɓasaá | ɛ→è, préfixes nasaux ǹ/ŋ́ préservés en écriture, simplifiés en audio | `ŋkap` → `nkap` |
| Ghɔmálá' | ŋ→ng, voyelles longues ee→é, oo→o | `ŋkap` → `ngkap` |
| Mə̀dûmbà | ə→e, diacritiques de ton retirés pour TTS | `mə̀dûmbà` → `medomba` |
| Fulfulde | implosives ɓ→b, ɗ→d, voyelles longues aa→a | `ɓoodi` → `boodi` |
| Haoussa | ɗ→d, ƴ→y, tons omis (Haoussa tonale mais TTS fr suffit) | `kuɗi` → `kudi` |
| Bulu | proche Ewondo : même règles | `mbôlô` → `mbolô` |
| Pidgin | corrections spécifiques Kamtok : moni→money, yu→you, go→go | lu en `en-US` |

### 4.4 Rapidité — Optimisations (v0.9.0)

| Mécanisme | Gain | Implémentation |
|---|---|---|
| Cache WAV navigateur (Map JS, 40 entrées) | 0 ms sur répétition | `voice_bridge.js` : `WAV_CACHE` |
| Cache ElevenLabs serveur (OrderedDict, 96 entrées) | Évite le 2e appel API | `phonetics.py` : `_ELEVENLABS_WAV_CACHE` |
| Préchauffe au chargement (`/api/audio/prefetch`) | 1–2 s économisées sur 1er clic | `voice_bridge.js` : `prefetchCurrentScreen()` |
| `Cache-Control: public, max-age=86400` | Évite re-transfert HTTP | Endpoint `/api/audio/tts` |
| Connexion HTTP persistante (`httpx.AsyncClient`) | Évite TCP handshake | `bank_client.py` |

---

## 5. Sécurité et Intégrité

### 5.1 Données personnelles

- **Aucun stockage persistant** des données client : la `SessionStore` est en mémoire (Python `dict`), perdue à l'arrêt du service.
- **Numéros de téléphone normalisés** uniquement pour le routage de session (`normalize_phone()`), jamais loggés avec les montants.
- **Clés API** : `.env` → `.gitignore` → aucune clé dans l'historique Git.

### 5.2 Intégrité du Code Source des Plateformes

La solution respecte l'exigence du challenge : *"sans que chaque institution financière ait besoin de modifier son code source"*.

- **Côté sandbox** : zéro modification du code SAFINUM. L'intégration se fait uniquement via l'endpoint `/middleware` déclaré dans le dashboard de l'équipe.
- **Extension navigateur** : injecte un `content_script` dans le DOM, sans modifier les fichiers JavaScript du sandbox. L'interception de `SpeechSynthesisUtterance.prototype.voice` est un Monkey-patch côté navigateur local, non un changement côté serveur.
- **Couche de traduction** : `ui_translator.py` traduit les gabarits reçus du sandbox et retourne les mêmes clés JSON attendues — le sandbox ne sait pas que la traduction a eu lieu.

### 5.3 Authenticité des Traductions

Toutes les traductions ont été croisées avec au moins une source primaire documentée (voir §3). Les cas où une seule source est disponible (Basaa, Mə̀dûmbà, Bulu) sont explicitement signalés comme "moyen" dans la section de vérification du README. Aucune traduction n'a été générée par un LLM sans vérification.

---

## 6. Limites Reconnues et Travail Futur

| Langue | Limite | Raison | Action prévue |
|---|---|---|---|
| Basaa (`bas`) | 2 sources primaires seulement | Peu de ressources web | Enregistrements natifs supplémentaires |
| Mə̀dûmbà (`byv`) | Corpus SOREVA uniquement | Langue peu dotée | Collaboration avec locuteurs natifs |
| Bulu (`bum`) | Proche Ewondo utilisé pour inférence | Peu de datasets distincts | Dataset Bulu-Français spécifique |
| Audio natif | 18 clips seulement | Contrainte de temps | Extension de l'outil de recording (`recorder.html`) |
| Tons lexicaux | Simplifiés pour TTS fr-FR | ElevenLabs ne supporte pas les tons camerounais | Modèle TTS dédié par langue (en développement) |

---

*Document généré le 2026-11-27 par l'équipe Dev space ICT — Safinum Lingua.*
*Sources primaires : OlameMend/soreva (CC-BY-4.0), datasets HuggingFace CC, Bible multilingue (domaine public), BBC Hausa, Wiktionnaire.*
