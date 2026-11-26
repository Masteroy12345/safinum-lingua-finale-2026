"""Service de traduction neuronale & correction de phrases entières (façon Google Traduction Pro).

Pipeline complet :
1. Détection de langue source (`fr`, `en`, `ewo`, `fub`, `dua`, `bas`, `bbj`, `byv`, `wes`).
2. Analyse et correction grammaticale/orthographique de phrase entière (`sentence_corrector.py` via T5).
3. Masquage strict des montants (FCFA/XAF), téléphones (+237/6XXXXXXXX), références (TRX-/SAF-) et facturiers.
4. Traduction complète via modèles locaux hors-ligne (`flagship-ai/cameroon-int8` CTranslate2 + `OPUS-MT-Bantu/Mul`)
   avec garde-fou terminologique SAFINUM (ou Claude API si clé configurée).
5. Phonétique IPA + Script vocal TTS optimisé + Synthèse WAV neurale locale (Meta MMS-TTS) + conformité GSM-7 USSD.
"""
from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(Path(__file__).with_name(".env"), override=False)
load_dotenv(ROOT / ".env", override=False)

# Monter safinum-middleware/app sous "safinum_mw" pour éviter tout conflit avec app.py
if "safinum_mw" not in sys.modules:
    _mw_pkg = types.ModuleType("safinum_mw")
    _mw_pkg.__path__ = [str(ROOT / "safinum-middleware" / "app")]
    sys.modules["safinum_mw"] = _mw_pkg

from safinum_mw.gsm7 import is_gsm7, septet_length, transliterate_to_gsm7
from safinum_mw.languages import CAMEROON_NATIONAL_LANGUAGES, SUPPORTED_LANGUAGES, detect_language, normalize_language, translate_phrase
from safinum_mw.phonetics import build_audio_payload, synthesize_wav_bytes
from local_nmt import available_models_status, translate_neural_local
from sentence_corrector import correct_sentence

app = FastAPI(
    title="Safinum Lingua — Service IA de Traduction & Correction (Style Google Traduction)",
    version="2.0.0",
    description="Analyse/corrige les phrases entières, protège les entités bancaires, traduit via modèles locaux hors-ligne et produit IPA + Audio.",
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

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


class CorrectRequest(BaseModel):
    text: str
    language: str | None = None


class TextTranslateRequest(BaseModel):
    text: str
    source_language: str | None = None
    target_language: str = "dua"
    auto_correct: bool = True


def _mask_sensitive(text: str) -> tuple[str, list[tuple[str, str]]]:
    pairs: list[tuple[str, str]] = []

    def _stash(m: re.Match) -> str:
        idx = len(pairs)
        # Sentinelle numérique unique préservée fidèlement par MarianMT/CTranslate2/T5
        sentinel = f"88010{idx}"
        while sentinel in text:
            sentinel = f"88{idx}10{idx}"
        pairs.append((sentinel, m.group(0)))
        return sentinel

    masked = _PROT_RE.sub(_stash, text)
    return masked, pairs


def _unmask_sensitive(text: str, pairs: list[tuple[str, str]]) -> str | None:
    out = text
    for sentinel, val in pairs:
        if out.count(sentinel) != 1:
            return None
        out = out.replace(sentinel, val)
    return out


async def _llm_translate(text: str, target_lang: str) -> str | None:
    if not ANTHROPIC_API_KEY:
        return None
    lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
    masked, pairs = _mask_sensitive(text)
    prompt = (
        f"Traduis fidèlement cette phrase financière complète en {lang_name} ({target_lang}). "
        f"Conserve exactement les nombres sentinelles ({', '.join(s for s, _ in pairs) or 'aucun'}) sans les modifier. "
        f"Retourne uniquement la traduction.\n\nTexte : {masked}"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-haiku-latest",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        if r.status_code == 200:
            content = r.json().get("content", [{}])[0].get("text", "").strip()
            if content:
                return _unmask_sensitive(content, pairs)
    except Exception:
        return None
    return None


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "safinum-service-google",
        "languages": list(SUPPORTED_LANGUAGES.keys()),
        "models": available_models_status(),
    }


@app.post("/correct")
async def correct_endpoint(req: CorrectRequest) -> dict[str, Any]:
    lang = normalize_language(req.language) or detect_language(req.text)
    return {"language": lang, **correct_sentence(req.text, lang)}


def _translate_chunked_preserving_entities(work_text: str, src: str, tgt: str) -> tuple[str | None, str]:
    """Traduit les segments autour des entités bancaires lorsque la NMT altère les sentinelles."""
    splitter = re.compile(f"({_PROT_RE.pattern})", flags=re.IGNORECASE)
    segments = splitter.split(work_text)
    rendered: list[str] = []
    engines: list[str] = []

    for seg in segments:
        if not seg:
            continue
        if _PROT_RE.fullmatch(seg.strip()):
            rendered.append(seg.strip())
            continue
        if not re.search(r"[A-Za-zÀ-ÿ]", seg):
            rendered.append(seg.strip())
            continue
        sub_out, sub_eng = translate_neural_local(seg.strip(), src, tgt)
        if sub_out:
            rendered.append(sub_out.strip())
            if sub_eng not in engines:
                engines.append(sub_eng)
        else:
            lex = translate_phrase(seg.strip(), tgt)
            rendered.append(lex["translated"])
            if lex["mode"] not in engines:
                engines.append(f"lex:{lex['mode']}")

    if not rendered:
        return None, "unavailable"
    joined = re.sub(r"\s+([.,!?;:])", r"\1", " ".join(p for p in rendered if p))
    return re.sub(r"\s{2,}", " ", joined).strip(), "+".join(engines) if engines else "chunked"


@app.post("/translate")
async def translate_text(req: TextTranslateRequest) -> dict[str, Any]:
    src = normalize_language(req.source_language) or detect_language(req.text)
    tgt = normalize_language(req.target_language) or "fr"

    # 1. Inspection & correction grammaticale/orthographique de la phrase entière
    corr = correct_sentence(req.text, src) if req.auto_correct else {
        "original": req.text,
        "corrected": req.text.strip(),
        "changed": False,
        "engine": "disabled",
        "protected_entities": [],
    }
    work_text = corr["corrected"] or req.text

    # 2. Masquage strict des entités financières avant traduction neuronale
    masked, pairs = _mask_sensitive(work_text)

    # 3. Priorité aux gabarits financiers naturels vérifiés si la phrase correspond exactement à un patron critique
    local_check = translate_phrase(work_text, tgt)
    if local_check["mode"] in ("exact_word", "natural_sentence"):
        translated = local_check["translated"]
        engine = f"verified_financial_{local_check['mode']}"
    else:
        # 4. Traduction neuronale locale (phrase entière puis repli segmenté autour des entités)
        nmt_raw, nmt_engine = translate_neural_local(masked, src, tgt)
        restored = _unmask_sensitive(nmt_raw, pairs) if nmt_raw else None
        if restored:
            translated = restored
            engine = nmt_engine
        else:
            chunked, chunk_eng = _translate_chunked_preserving_entities(work_text, src, tgt) if pairs else (None, "none")
            if chunked:
                translated = chunked
                engine = f"{chunk_eng}+entity_segmented"
            else:
                # 5. Repli LLM externe (si clé API) ou lexique déterministe local
                llm_out = await _llm_translate(work_text, tgt)
                if llm_out:
                    translated = llm_out
                    engine = "neural_llm"
                else:
                    translated = local_check["translated"]
                    engine = f"local_{local_check['mode']}"

    audio = build_audio_payload(translated, tgt)
    gsm7_text = transliterate_to_gsm7(translated)
    return {
        "source_language": src,
        "target_language": tgt,
        "source_text": req.text,
        "corrected_text": work_text,
        "correction_applied": corr["changed"],
        "correction_engine": corr["engine"],
        "protected_entities": corr["protected_entities"],
        "translated_text": translated,
        "engine": engine,
        "ipa": audio["ipa"],
        "web_phonetic": audio["web_phonetic"],
        "tts_script": audio["tts_script"],
        "tts_voice_lang": audio["tts_voice_lang"],
        "neural_tts_available": audio["neural_tts_available"],
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
    opts = "".join(f'<option value="{k}" {"selected" if k=="ewo" else ""}>{v} ({k})</option>' for k, v in CAMEROON_NATIONAL_LANGUAGES.items())
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Safinum Lingua — Traducteur IA & Correcteur de Phrases (Dev space ICT)</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 28px; }}
  .wrap {{ max-width: 1020px; margin: 0 auto; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 18px; }}
  textarea, select {{ width: 100%; box-sizing: border-box; background: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 10px; padding: 12px; font-size: 15px; }}
  textarea {{ min-height: 150px; resize: vertical; }}
  button {{ background: #10b981; color: #0f172a; font-weight: 700; border: none; border-radius: 10px; padding: 11px 20px; cursor: pointer; font-size: 14px; margin-top: 10px; margin-right: 8px; }}
  .corr {{ margin-top: 10px; padding: 10px 12px; background: #172554; border: 1px solid #3b82f6; border-radius: 8px; font-size: 13px; display: none; }}
  .meta {{ margin-top: 10px; padding: 10px 12px; background: #1e293b; border-radius: 8px; font-size: 13px; color: #cbd5e1; line-height: 1.6; }}
  .pill {{ display: inline-block; background: #064e3b; color: #6ee7b7; padding: 2px 8px; border-radius: 999px; font-size: 12px; margin-right: 6px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1 style="margin:0;">Safinum Lingua Translate Pro <span style="color:#10b981;font-size:15px;">• Modèles IA &amp; Correction Complète</span></h1>
  <p style="color:#94a3b8;">Corrige d'abord les phrases entières (T5), protège les montants/numéros/références, traduit hors-ligne (CTranslate2 / OPUS-MT) et génère IPA + Audio.</p>
  <div style="margin-top:10px;">
    <button onclick="preset('bonjor je veu envoye 5 000 FCFA a 677000001 sil vou plait')" style="background:#334155;color:#e2e8f0;">Ex. FR avec fautes</button>
    <button onclick="preset('Combien coutent les frais pour envoyer 25 000 FCFA ?')" style="background:#334155;color:#e2e8f0;">Ex. Frais</button>
    <button onclick="preset('I wants to checks my account balance before sending 10 000 FCFA.')" style="background:#334155;color:#e2e8f0;">Ex. EN avec fautes</button>
  </div>
  <div class="grid">
    <div>
      <label>Texte source (auto-détecté + correction T5)</label>
      <textarea id="src">bonjor je veu envoye 5 000 FCFA a 677000001 sil vou plait</textarea>
      <label style="display:block;margin-top:8px;font-size:13px;"><input type="checkbox" id="autocorr" checked> Corriger la phrase entière automatiquement avant traduction</label>
      <button onclick="doTranslate()">Corriger &amp; Traduire</button>
      <div class="corr" id="corr"></div>
    </div>
    <div>
      <label>Langue cible</label>
      <select id="tgt">{opts}</select>
      <textarea id="out" readonly style="margin-top:10px;" placeholder="Traduction..."></textarea>
      <div class="meta" id="meta"></div>
      <div style="margin-top:10px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <button onclick="speak()" style="background:#38bdf8;margin-top:0;">🔊 Réécouter (Voix Homme)</button>
        <label style="font-size:13px;color:#6ee7b7;"><input type="checkbox" id="autospeak" checked> 🔊 Voix générée auto selon le texte</label>
        <audio id="autoWav3001" controls style="height:30px;"></audio>
      </div>
    </div>
  </div>
</div>
<script>
let lastData = {{ tts_script: "", tts_voice_lang: "fr" }};
function preset(txt) {{
  document.getElementById('src').value = txt;
  doTranslate();
}}
async function doTranslate() {{
  const r = await fetch('/translate', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{
      text: document.getElementById('src').value,
      target_language: document.getElementById('tgt').value,
      auto_correct: document.getElementById('autocorr').checked
    }})
  }});
  const d = await r.json();
  lastData = d;
  document.getElementById('out').value = d.translated_text;
  const corrEl = document.getElementById('corr');
  if (d.correction_applied) {{
    corrEl.style.display = 'block';
    corrEl.innerHTML = `<b>Phrase corrigée (${{d.correction_engine}}) :</b> ${{d.corrected_text}}`;
  }} else {{
    corrEl.style.display = 'block';
    corrEl.innerHTML = `<b>Phrase validée (${{d.correction_engine}}) :</b> ${{d.corrected_text}}`;
  }}
  document.getElementById('meta').innerHTML =
    `<span class="pill">Source: ${{d.source_language}}</span>` +
    `<span class="pill">Moteur: ${{d.engine}}</span>` +
    `<span class="pill">GSM-7: ${{d.gsm7_septets}}/182</span><br>` +
    `<b>IPA :</b> ${{d.ipa}}<br>` +
    `<b>Prononciation TTS :</b> ${{(d.tts_engine === 'elevenlabs-male' && d.elevenlabs_native_text) ? d.elevenlabs_native_text : d.tts_script}}<br>` +
    `<b>Version Web vocale :</b> ${{d.web_phonetic}}`;
  if (d.translated_text) {{
    const url = `/tts?text=${{encodeURIComponent(d.translated_text)}}&language=${{encodeURIComponent(d.target_language)}}`;
    const p = document.getElementById('autoWav3001');
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
  if (!lastData.translated_text) return;
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  const p = document.getElementById('autoWav3001');
  if (p) {{
    const url = `/tts?text=${{encodeURIComponent(lastData.translated_text)}}&language=${{encodeURIComponent(lastData.target_language)}}`;
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
