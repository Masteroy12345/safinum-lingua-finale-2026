"""Module d'analyse et de correction orthographique/grammaticale de phrases entières.

Utilise des modèles T5 téléchargés en local :
- Français : `models/t5-spell-fr` (`fdemelo/t5-base-spell-correction-fr`, préfixe `"grammaire: "`)
- Anglais  : `models/t5-grammar-en` (`vennify/t5-base-grammar-correction`, préfixe `"grammar: "`)

Protège strictement les montants (FCFA/XAF), numéros camerounais (+237/6XXXXXXXX),
références (TRX-/SAF-), et noms d'opérateurs/facturiers avant toute correction.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = Path(os.getenv("SAFINUM_MODELS_DIR", str(ROOT_DIR / "models")))
ENABLE_AI_CORRECTOR = os.getenv("ENABLE_AI_CORRECTOR", "1") == "1"

_SENSITIVE_RE = re.compile(
    r"(?:TRX|SAF)-[A-Z0-9\-]+|"
    r"(?:\+?237[\s\-\.]?)?6[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}|"
    r"\b\d[\d\s\.,]*\s*(?:FCFA|XAF)\b|"
    r"\b(?:ENEO|CAMWATER|CANAL|CAMTEL|MTN|ORANGE|SAFINUM)\b",
    flags=re.IGNORECASE,
)


def _mask_numeric_sentinels(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Remplace chaque entité sensible par un sentinelle numérique unique que T5 ne modifie pas."""
    pairs: list[tuple[str, str]] = []

    def _stash(m: re.Match) -> str:
        idx = len(pairs)
        sentinel = f"99010{idx}"
        while sentinel in text:
            sentinel = f"99{idx}10{idx}"
        pairs.append((sentinel, m.group(0)))
        return sentinel

    masked = _SENSITIVE_RE.sub(_stash, text)
    return masked, pairs


def _unmask_numeric_sentinels(text: str, pairs: list[tuple[str, str]]) -> str | None:
    out = text
    for sentinel, original in pairs:
        if out.count(sentinel) != 1:
            return None
        out = out.replace(sentinel, original)
    return out


def _rule_normalize_sentence(text: str, lang: str) -> str:
    """Normalisation rapide déterministe pour préserver les termes financiers camerounais."""
    s = re.sub(r"\s{2,}", " ", text.strip())
    if lang == "fr":
        # Prétraitement ciblé des fautes SMS/orales courantes avant passage dans T5
        repl = [
            (r"\bbonjor\b", "bonjour"),
            (r"\bmerc[iy]\b", "merci"),
            (r"\bje veu\b", "je veux"),
            (r"\btu veu\b", "tu veux"),
            (r"\bil veu\b", "il veut"),
            (r"\bon veu\b", "on veut"),
            (r"\benvoye\b", "envoyer"),
            (r"\btransferer\b", "transférer"),
            (r"\bverifie\b", "vérifier"),
            (r"\bcombien jai\b", "combien j'ai"),
            (r"\bjai\b", "j'ai"),
            (r"\bcest\b", "c'est"),
            (r"\bsil vou plait\b", "s'il vous plaît"),
            (r"\bsvp\b", "s'il vous plaît"),
            (r"\bkil\b", "qu'il"),
            (r"\baujourdhui\b", "aujourd'hui"),
            (r"\bmon frere\b", "mon frère"),
        ]
        for pat, dst in repl:
            s = re.sub(pat, dst, s, flags=re.IGNORECASE)
    elif lang == "en":
        repl_en = [
            (r"\bI wants\b", "I want"),
            (r"\bto checks\b", "to check"),
            (r"\bplz\b", "please"),
            (r"\bthx\b", "thanks"),
        ]
        for pat, dst in repl_en:
            s = re.sub(pat, dst, s, flags=re.IGNORECASE)
    return s


@lru_cache(maxsize=2)
def _load_t5(model_dirname: str):
    model_path = MODELS_DIR / model_dirname
    if not model_path.is_dir():
        return None, None
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
        mod = AutoModelForSeq2SeqLM.from_pretrained(str(model_path), local_files_only=True)
        mod.eval()
        return tok, mod
    except Exception:
        return None, None


@lru_cache(maxsize=256)
def _run_t5_cached(dirname: str, prefix: str, pre_norm: str) -> str | None:
    tok, mod = _load_t5(dirname)
    if not tok or not mod:
        return None
    try:
        import torch

        inputs = tok(f"{prefix}{pre_norm}", return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            out_ids = mod.generate(
                **inputs,
                num_beams=1,
                min_length=1,
                max_new_tokens=160,
            )
        return tok.decode(out_ids[0], skip_special_tokens=True).strip()
    except Exception:
        return None


def correct_sentence(text: str, language: str = "fr") -> dict[str, Any]:
    """Inspecte et corrige une phrase entière (orthographe, accents, grammaire, ponctuation)."""
    raw = (text or "").strip()
    if not raw:
        return {"original": raw, "corrected": raw, "changed": False, "engine": "noop", "protected_entities": []}

    lang = (language or "fr").lower()
    masked, sentinels = _mask_numeric_sentinels(raw)
    protected_entities = [orig for _, orig in sentinels]
    pre_norm = _rule_normalize_sentence(masked, lang)

    if ENABLE_AI_CORRECTOR and lang in ("fr", "en") and len(raw.split()) >= 2:
        dirname = "t5-spell-fr" if lang == "fr" else "t5-grammar-en"
        prefix = "grammaire: " if lang == "fr" else "grammar: "
        cand = _run_t5_cached(dirname, prefix, pre_norm)
        if cand:
            restored = _unmask_numeric_sentinels(cand, sentinels)
            word_ratio_ok = max(1, len(pre_norm.split()) // 2) <= len(cand.split()) <= len(pre_norm.split()) * 2 + 2
            if restored and word_ratio_ok:
                return {
                    "original": raw,
                    "corrected": restored,
                    "changed": restored != raw,
                    "engine": f"{dirname}+financial_guard",
                    "protected_entities": protected_entities,
                }

    restored_rule = _unmask_numeric_sentinels(pre_norm, sentinels) or raw
    return {
        "original": raw,
        "corrected": restored_rule,
        "changed": restored_rule != raw,
        "engine": "deterministic_normalizer",
        "protected_entities": protected_entities,
    }
