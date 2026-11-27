"""Canal IVR (Serveur Vocal Interactif) — Safinum Innovate Challenge 2026.

Contrat :
- input.type == "dtmf"  → saisie clavier (chiffre ou vide au décroché)
- input.type == "audio" → WAV PCM 16 bits mono base64 (8 ou 16 kHz, max 30s)
  → transcription via Gemini 1.5 Flash audio  → NLU → réponse texte <= 400 chars
- Réponse : même contrat USSD (response.text, interpretation.intent, transaction)
  mais max_chars = 400, charset = utf8, mode = voice
"""
from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import httpx

from .config import settings
from .gsm7 import fit_channel_constraints
from .languages import normalize_language

logger = logging.getLogger(__name__)

# URL Gemini 1.5 Flash — transcription audio + compréhension
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)
_GEMINI_STT_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

IVR_MAX_CHARS = 400


async def transcribe_audio_gemini(
    audio_b64: str,
    sample_rate: int,
    language: str | None,
) -> str:
    """Transcrit un audio WAV base64 via Gemini 1.5 Flash.

    Renvoie le texte transcrit ou '' si Gemini échoue.
    """
    api_key = settings.gemini_api_key
    if not api_key:
        logger.warning("[IVR] GEMINI_API_KEY absent — transcription impossible")
        return ""

    # Construire la langue de transcription pour le prompt
    lang_hint = ""
    if language:
        lang_map = {
            "dua": "Duálá (langue bantoue du Cameroun)",
            "ewo": "Ewondo (langue bantoue du Cameroun)",
            "bas": "Ɓasaá (langue bantoue du Cameroun)",
            "bbj": "Ghɔmálá' (langue grassfield du Cameroun)",
            "byv": "Mə̀dûmbà (langue grassfield du Cameroun)",
            "fub": "Fulfulde (langue afro-asiatique du Cameroun)",
            "hau": "Haoussa (langue afro-asiatique)",
            "bum": "Bulu (langue bantoue du Cameroun)",
            "wes": "Pidgin Camerounais (créole anglais)",
            "fr": "Français",
            "en": "Anglais",
        }
        lang_hint = lang_map.get(language, language)

    prompt = (
        f"Transcris exactement ce que dit la personne dans cet enregistrement audio. "
        f"La langue parlée est : {lang_hint or 'inconnue, détecte-la'}. "
        "Ne traduis pas, ne corrige pas la grammaire, ne commente pas. "
        "Retourne UNIQUEMENT le texte transcrit."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "audio/wav",
                            "data": audio_b64,
                        }
                    },
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 512,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_GEMINI_URL}?key={api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if not resp.is_success:
                logger.error("[IVR] Gemini STT HTTP %d: %s", resp.status_code, resp.text[:200])
                return ""
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            text = " ".join(p.get("text", "") for p in parts).strip()
            logger.info("[IVR] Gemini transcription: %r", text[:80])
            return text
    except Exception as exc:
        logger.error("[IVR] Gemini STT error: %s", exc)
        return ""


async def handle_ivr_audio(
    audio_payload: dict[str, Any],
    language: str | None,
) -> str:
    """Extrait l'audio du payload IVR et renvoie la transcription."""
    if not audio_payload:
        return ""
    b64_data = audio_payload.get("data", "")
    sample_rate = audio_payload.get("sample_rate", 8000)
    if not b64_data:
        return ""
    return await transcribe_audio_gemini(b64_data, sample_rate, language)


def build_ivr_response_text(text: str, channel: str = "ivr") -> str:
    """Tronque la réponse IVR à 400 caractères UTF-8 (contrat vocal)."""
    if not text:
        return ""
    fitted, _ = fit_channel_constraints(
        text,
        channel=channel,
        max_chars=IVR_MAX_CHARS,
        charset="utf8",
    )
    return fitted
