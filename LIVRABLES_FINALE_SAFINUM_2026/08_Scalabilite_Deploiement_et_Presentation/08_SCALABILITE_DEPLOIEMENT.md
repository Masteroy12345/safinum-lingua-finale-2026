# 8. Potentiel de Scalabilité, Déploiement & Vision

Ce dossier inclut également la présentation complète du jury : **`Safinum_Lingua_Presentation_Dev_Space_ICT.pptx`**.

## Performances & Coût d'infrastructure
- **Latence ultra-faible** : FastAPI asynchrone + CTranslate2 int8 CPU (~50–250 ms) sans dépendance GPU coûteuse, compatible avec les contraintes temps réel télécoms (`<= 3 s` en USSD, `<= 10 s` sur Mobile/Web).
- **100 % Souverain & Hors-ligne** : Tous les modèles IA (correction T5, traduction `cameroon-int8` / `OPUS-MT`, synthèse `MMS-TTS`) tournent en local sans fuite de données bancaires vers des API cloud tierces.
- **Mise en cache intelligente** : Les écrans `ui_translation` (89 clés) sont servis depuis le cache en `< 5 ms`.

## Scalabilité horizontale & Extensibilité linguistique
- **Ajout d'une nouvelle langue nationale** : grâce au bundle `flagship-ai/cameroon-int8` (60 langues camerounaises disponibles : Bafia, Yemba, Bulu, Tupuri, Fe'fe', Lamnso, etc.) et à l'architecture modulaire `UI_TRANSLATIONS` + `WORD_GLOSSARY`, l'ajout d'une langue supplémentaire ne nécessite aucune modification du moteur ni des applications bancaires.
- **Déploiement multi-banques / CEMAC** : une seule instance Docker/Kubernetes mutualisée peut servir plusieurs institutions financières via l'en-tête `X-Team-Key` / `team_id` et la résolution dynamique de `bank_api.base_url`.

## Feuille de route v2 (Canaux déjà pré-câblés)
- **SMS asynchrone** : découpage et comptage exact des segments GSM-7 (`160` / `153`) pour maîtriser les coûts opérateurs.
- **Guichets Automatiques (ATM/GAB)** : support des saisies numériques et contrainte de coupures multiples de `5 000 FCFA`.
- **Serveur Vocal Interactif (IVR)** : intégration directe d'un module ASR (`Wav2Vec2` / `Whisper`) sur flux WAV `16 kHz / 8 kHz` couplé à nos modèles vocaux `MMS-TTS` et à notre couche phonétique.
