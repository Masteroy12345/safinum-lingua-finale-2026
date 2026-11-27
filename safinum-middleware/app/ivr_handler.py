"""Canal IVR (Serveur Vocal Interactif) — Safinum Innovate Challenge 2026.

Contrat :
- input.type == "dtmf"  → saisie clavier (chiffre ou vide au décroché)
- input.type == "audio" → WAV PCM 16 bits mono base64 (8 ou 16 kHz, max 30s)
  → transcription via Gemini 2.0 Flash Lite  → NLU → réponse texte <= 400 chars
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

# Gemini 2.0 Flash Lite — transcription audio + compréhension
_GEMINI_MODEL = "gemini-2.0-flash-lite"
_GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{_GEMINI_MODEL}:generateContent"
)
_GEMINI_STT_URL = _GEMINI_URL

IVR_MAX_CHARS = 400


_LANG_NAMES = {
    "dua": "Duálá (Bantu, Cameroun)",
    "ewo": "Ewondo (Bantu, Cameroun)",
    "bas": "Ɓasaá (Bantu, Cameroun)",
    "bbj": "Ghɔmálá' (Grassfield, Cameroun)",
    "byv": "Mə̀dûmbà (Grassfield, Cameroun)",
    "fub": "Fulfulde (Afro-Asiatique, Cameroun)",
    "hau": "Haoussa (Afro-Asiatique)",
    "bum": "Bulu (Bantu, Cameroun)",
    "wes": "Pidgin Camerounais (créole anglais)",
    "fr":  "Français",
    "en":  "Anglais",
}


async def transcribe_audio_gemini(
    audio_b64: str,
    sample_rate: int,
    language: str | None,
) -> str:
    """Transcrit un audio WAV base64 via Gemini 2.0 Flash Lite.

    Renvoie le texte transcrit ou '' si Gemini échoue.
    """
    api_key = settings.gemini_api_key
    if not api_key:
        logger.warning("[IVR] GEMINI_API_KEY absent — transcription impossible")
        return ""

    lang_hint = _LANG_NAMES.get(language or "", language or "inconnue, à détecter")

    # Le WAV peut être 8 kHz (bande téléphonique) ou 16 kHz.
    # Gemini accepte audio/wav dans les deux cas.
    prompt = (
        f"Écoute cet enregistrement audio téléphonique. "
        f"La langue parlée est : {lang_hint}. "
        "Transcris exactement ce que dit la personne, mot pour mot. "
        "Si tu n'entends qu'un silence, retourne la chaîne vide. "
        "Ne traduis pas, ne corrige pas la grammaire, ne commente pas. "
        "Retourne UNIQUEMENT le texte transcrit, sans guillemets ni ponctuation ajoutée."
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
            "temperature": 0.0,
            "maxOutputTokens": 256,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{_GEMINI_URL}?key={api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if not resp.is_success:
                logger.error("[IVR] Gemini STT HTTP %d: %s", resp.status_code, resp.text[:300])
                return ""
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                logger.warning("[IVR] Gemini: aucun candidat — finish_reason: %s",
                               data.get("promptFeedback", {}).get("blockReason", "?"))
                return ""
            finish = candidates[0].get("finishReason", "")
            parts = candidates[0].get("content", {}).get("parts", [])
            text = " ".join(p.get("text", "") for p in parts).strip()
            logger.info("[IVR] Gemini 2.0 Flash Lite transcription (%s): %r (finish=%s)",
                        language, text[:100], finish)
            return text
    except httpx.TimeoutException:
        logger.error("[IVR] Gemini STT timeout (20s)")
        return ""
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
