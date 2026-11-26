# Safinum Lingua — Middleware Universel (Port 3000)

Middleware REST multicanal de l'équipe **Dev space ICT** conforme à 100 % au bac à sable officiel [safinum.cm/sandbox/docs](https://www.safinum.cm/sandbox/docs) :
- **Canal USSD (`*123#`)** : NLU 13 intentions (+ repli CTranslate2), API bancaire avec propagation stricte `X-Team-Key` + `X-Trace-Id`, confirmation en 2 tours séparés, `options: list[str]`, translittération et compteur GSM-7 (`<= 182` septets).
- **Canaux Mobile & Web (`type == "ui_translation"`)** : traduction complète des **89 clés officielles** sur 6 écrans (`home`, `transfer`, `pay`, `review`, `receipt`, `history`) dans les 9 langues, emplacements `{amount}`, `{name}`, `{fee}`, `{missing}`, `{max}` intacts, respect strict des `max_chars` et adaptation phonétique pour le lecteur vocal `fr-FR` du sandbox.
- **Audio & Phonétique** : endpoints `/api/grammar`, `/api/phonetics`, `/api/translate`, `/api/audio/tts` (WAV neural Meta MMS-TTS local + IPA + script TTS guidé).

## Démarrage & Tests

```bash
cp .env.example .env
../.venv/bin/pytest -v
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3000
```

Sous Windows : `start.bat` et `.\register_endpoints.ps1 -TeamKey "sbx_..." -PublicUrl "https://..."`.
