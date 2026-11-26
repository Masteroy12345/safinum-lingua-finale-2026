"""Système de traduction lexicale mot-à-mot avec alignement token-par-token et protection financière — Dev space ICT."""
from __future__ import annotations

import json
import os
import re
import sys
import types
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(Path(__file__).with_name(".env"), override=False)
load_dotenv(ROOT / ".env", override=False)

# Monter safinum-middleware/app sous le nom "safinum_mw" pour ne pas entrer en conflit avec app.py
if "safinum_mw" not in sys.modules:
    _mw_pkg = types.ModuleType("safinum_mw")
    _mw_pkg.__path__ = [str(ROOT / "safinum-middleware" / "app")]
    sys.modules["safinum_mw"] = _mw_pkg

from safinum_mw.gsm7 import is_gsm7, septet_length, transliterate_to_gsm7
from safinum_mw.languages import (
    CAMEROON_NATIONAL_LANGUAGES,
    SUPPORTED_LANGUAGES,
    WORD_GLOSSARY,
    _CONNECTORS,
    _DROP_ARTICLES,
    _EN_TO_GLOSSARY_KEY,
    normalize_language,
)
from safinum_mw.phonetics import build_audio_payload, synthesize_wav_bytes

app = FastAPI(
    title="Safinum Lingua — Traduction Mot-à-Mot",
    version="2.0.0",
    description="Approche lexicale mot-à-mot dans les 9 langues avec alignement token-par-token, protection financière stricte, phonétique IPA et conformité GSM-7.",
)

_PROT_RE = re.compile(
    r"\{[a-z_]+\}|"
    r"(?:TRX|SAF)-[A-Za-z0-9\-]+|"
    r"(?:\+?237[\s\-\.]?)?6[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}|"
    r"\b\d[\d\s\.,]*\s*(?:FCFA|XAF|CFA)\b|"
    r"\b(?:FCFA|XAF|CFA)\b|"
    r"\b\d+(?:[\s\.,]\d+)*\b|"
    r"\b(?:ENEO|CAMWATER|CANAL\+?|CAMTEL|MTN|ORANGE|SAFINUM(?:\s+PAY)?)\b",
    flags=re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _load_fub_corpus_lexicon() -> dict[str, str]:
    p = ROOT / "safinum-middleware" / "app" / "data" / "cameroon_corpus_extract.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {k.lower(): v for k, v in (data.get("fulfulde_fr_lexicon") or {}).items()}
    except Exception:
        return {}


class TranslateRequest(BaseModel):
    text: str
    target_language: str = "dua"


def word_by_word_translate(text: str, target_lang: str) -> dict[str, Any]:
    lang = normalize_language(target_lang) or "fr"
    clean = text.strip()
    protected: list[str] = []

    def _stash(m: re.Match) -> str:
        idx = len(protected)
        protected.append(m.group(0))
        return f"__PROT_{idx}__"

    masked = _PROT_RE.sub(_stash, clean)
    tokens = re.findall(r"__PROT_\d+__|[A-Za-zÀ-ÿ0-9'ʼ]+|[^\w\s]+|\s+", masked)

    alignments: list[dict[str, str]] = []
    out_parts: list[str] = []
    replaced = 0

    for tok in tokens:
        if tok.isspace():
            out_parts.append(tok)
            continue
        if tok.startswith("__PROT_"):
            idx = int(tok.replace("__PROT_", "").replace("__", ""))
            orig_val = protected[idx]
            out_parts.append(orig_val)
            alignments.append({"source": orig_val, "target": orig_val, "status": "protected"})
            continue
        if not re.match(r"^[A-Za-zÀ-ÿ'ʼ]+$", tok):
            out_parts.append(tok)
            alignments.append({"source": tok, "target": tok, "status": "punctuation"})
            continue

        norm_tok = tok.lower().replace("é", "e").replace("è", "e").replace("ê", "e")
        if lang != "fr" and norm_tok in _DROP_ARTICLES:
            alignments.append({"source": tok, "target": "", "status": "dropped_article"})
            continue
        if norm_tok in _CONNECTORS:
            tr = _CONNECTORS[norm_tok].get(lang, tok)
            out_parts.append(tr)
            alignments.append({"source": tok, "target": tr, "status": "connector"})
            replaced += 1
            continue
        g_key = _EN_TO_GLOSSARY_KEY.get(norm_tok, norm_tok)
        if g_key in WORD_GLOSSARY:
            tr = WORD_GLOSSARY[g_key].get(lang, tok)
            out_parts.append(tr)
            alignments.append({"source": tok, "target": tr, "status": "translated"})
            replaced += 1
        elif lang == "fub" and (tok.lower() in _load_fub_corpus_lexicon() or norm_tok in _load_fub_corpus_lexicon()):
            fub_lex = _load_fub_corpus_lexicon()
            tr = fub_lex.get(tok.lower()) or fub_lex[norm_tok]
            out_parts.append(tr)
            alignments.append({"source": tok, "target": tr, "status": "translated"})
            replaced += 1
        else:
            # Repli neuronal sur mot inconnu du lexique
            nmt_word = None
            if lang != "fr":
                try:
                    nmt_dir = str(ROOT / "traduction_service_google")
                    if nmt_dir not in sys.path:
                        sys.path.insert(0, nmt_dir)
                    from local_nmt import translate_neural_local

                    cand_out, _ = translate_neural_local(tok, "fr", lang)
                    if cand_out and cand_out.strip().lower() != tok.lower():
                        nmt_word = cand_out.strip().rstrip(".")
                except Exception:
                    pass
            if nmt_word:
                out_parts.append(nmt_word)
                alignments.append({"source": tok, "target": nmt_word, "status": "translated"})
                replaced += 1
            else:
                out_parts.append(tok)
                alignments.append({"source": tok, "target": tok, "status": "untouched"})

    translated = re.sub(r"\s{2,}", " ", "".join(out_parts)).strip()
    mode = "exact_word" if len(alignments) == 1 and replaced == 1 else ("word_by_word" if replaced > 0 else "passthrough")
    return {
        "mode": mode,
        "translated": translated,
        "words_translated": replaced,
        "alignments": alignments,
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "safinum-mot-a-mot", "languages": list(SUPPORTED_LANGUAGES.keys())}


@app.get("/glossary")
async def get_glossary():
    return {"languages": SUPPORTED_LANGUAGES, "words": WORD_GLOSSARY}


@app.post("/translate")
async def translate_word_by_word(req: TranslateRequest):
    lang = normalize_language(req.target_language) or "fr"
    res = word_by_word_translate(req.text, lang)
    audio = build_audio_payload(res["translated"], lang)
    gsm7_text = transliterate_to_gsm7(res["translated"])
    return {
        "input": req.text,
        "target_language": lang,
        **res,
        **audio,
        "gsm7_preview": gsm7_text,
        "gsm7_septets": septet_length(gsm7_text),
        "gsm7_strict": is_gsm7(gsm7_text),
    }


@app.post("/tts")
@app.get("/tts")
async def tts_endpoint(text: str = "", language: str = "fr"):
    lang = normalize_language(language) or "fr"
    wav, info = synthesize_wav_bytes(text, lang)
    if wav:
        return Response(content=wav, media_type="audio/wav", headers={"X-TTS-Engine": info})
    return JSONResponse({"fallback": "browser_tts", "reason": info, **build_audio_payload(text, lang)})


@app.get("/", response_class=HTMLResponse)
async def ui() -> str:
    opts = "".join(f'<option value="{k}" {"selected" if k=="dua" else ""}>{v} ({k})</option>' for k, v in CAMEROON_NATIONAL_LANGUAGES.items())
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Safinum Lingua — Traduction Mot-à-Mot</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 32px; }}
  .wrap {{ max-width: 960px; margin: 0 auto; }}
  textarea, select {{ width: 100%; box-sizing: border-box; background: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 10px; padding: 12px; font-size: 15px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 18px; }}
  button {{ background: #10b981; color: #0f172a; font-weight: 700; border: none; border-radius: 10px; padding: 11px 20px; cursor: pointer; font-size: 14px; margin-top: 10px; }}
  .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }}
  .chip {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 6px 10px; font-size: 13px; }}
  .chip.translated {{ border-color: #10b981; }}
  .chip.protected {{ border-color: #f59e0b; color: #fcd34d; }}
  .meta {{ margin-top: 10px; font-size: 13px; color: #94a3b8; }}
</style>
</head>
<body>
<div class="wrap">
  <h1 style="margin:0;">Safinum Lingua — Mode Mot-à-Mot Lexical <span style="color:#10b981;font-size:14px;">• Port 3002</span></h1>
  <p style="color:#94a3b8;">Traduction lexicale mot-par-mot avec alignement visible, protection des montants/téléphones et phonétique IPA/TTS.</p>
  <div class="grid">
    <div>
      <label>Texte source</label>
      <textarea id="src" rows="4">bonjour envoyer 5 000 FCFA à 677000001</textarea>
      <button onclick="doTranslate()">Traduire mot-à-mot</button>
    </div>
    <div>
      <label>Langue cible</label>
      <select id="tgt">{opts}</select>
      <textarea id="out" rows="4" readonly style="margin-top:8px;"></textarea>
      <div class="meta" id="meta"></div>
      <div style="margin-top:10px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <button onclick="speak()" style="background:#38bdf8;margin-top:0;">🔊 Réécouter (Voix Homme)</button>
        <label style="font-size:13px;color:#6ee7b7;"><input type="checkbox" id="autospeak" checked> 🔊 Voix générée auto selon le texte</label>
        <audio id="autoWav3002" controls style="height:30px;"></audio>
      </div>
    </div>
  </div>
  <div class="chips" id="chips"></div>
</div>
<script>
let lastData = {{}};
async function doTranslate() {{
  const r = await fetch('/translate', {{
    method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ text: document.getElementById('src').value, target_language: document.getElementById('tgt').value }})
  }});
  const d = await r.json();
  lastData = d;
  document.getElementById('out').value = d.translated;
  document.getElementById('meta').innerText = `Mode: ${{d.mode}} | IPA: ${{d.ipa}} | Audio ElevenLabs/TTS: ${{(d.tts_engine === 'elevenlabs-male' && d.elevenlabs_native_text) ? d.elevenlabs_native_text : d.tts_script}} | GSM-7: ${{d.gsm7_septets}}/182 septets`;
  document.getElementById('chips').innerHTML = (d.alignments || []).map(a =>
    `<div class="chip ${{a.status}}"><b>${{a.source}}</b> → ${{a.target || '(suppr.)'}} <small style="color:#94a3b8;">[${{a.status}}]</small></div>`
  ).join('');
  if (d.translated) {{
    const url = `/tts?text=${{encodeURIComponent(d.translated)}}&language=${{encodeURIComponent(d.target_language)}}`;
    const p = document.getElementById('autoWav3002');
    if (p) {{
      p.pause();
      p.src = url;
    }}
    if (document.getElementById('autospeak')?.checked) {{
      speak();
    }}
  }}
}}
async function speak() {{
  if (!lastData.translated) return;
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  const p = document.getElementById('autoWav3002');
  if (p) {{
    const url = `/tts?text=${{encodeURIComponent(lastData.translated)}}&language=${{encodeURIComponent(lastData.target_language)}}`;
    if (!p.src || !p.src.endsWith(url)) p.src = url;
    p.pause();
    p.currentTime = 0;
    p.play().catch(() => {{}});
  }}
}}
doTranslate();
</script>
</body>
</html>"""
