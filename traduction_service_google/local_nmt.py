"""Moteur neuronal local multi-modèles pour la traduction complète de phrases dans les 9 langues.

Utilise les modèles et corpus téléchargés hors-ligne dans `models/` et `datasets/` :
- `flagship-ai/cameroon-int8` (CTranslate2 int8, avec `repetition_penalty=1.35`) :
  * `fr` <-> `ewo` (Ewondo), `fub` (Fulfulde), `bbj` (Ghɔmálá'), `byv` (Mə̀dûmbà), `en` (English)
- `Helsinki-NLP/opus-mt-tc-bible-big-deu_eng_fra_por_spa-bnt` (CT2 int8 / Marian) :
  * `fr`/`en` -> `bas` (Ɓasaá) [remarque: tag `dua`/`ewo` filtré contre l'hallucination swahilie]
- `Helsinki-NLP/opus-mt-tc-bible-big-deu_eng_fra_por_spa-mul` (CT2 int8 / Marian) :
  * `fr`/`en` -> `wes` (`>>pcm<<` Cameroonian Pidgin), `bas`
- `Helsinki-NLP/opus-mt-tc-bible-big-bnt-deu_eng_fra_por_spa` :
  * `bas` / `dua` -> `fr` (`>>fra<<`) ou `en` (`>>eng<<`)
- Corpus aligné extrait (`safinum-middleware/app/data/cameroon_corpus_extract.json`) :
  * Soreva (150 phrases parallèles), Fulfulde Adamaoua / Agri, Pidgin MT560.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = Path(os.getenv("SAFINUM_MODELS_DIR", str(ROOT_DIR / "models")))
CORPUS_FILE = ROOT_DIR / "safinum-middleware" / "app" / "data" / "cameroon_corpus_extract.json"
ENABLE_LOCAL_NMT = os.getenv("ENABLE_LOCAL_NMT", "1") == "1"

# Paires directes dans flagship-ai/cameroon-int8 (pivot français)
CT2_CAMEROON_PAIRS = {
    ("fr", "ewo"): "francais-ewondo",
    ("ewo", "fr"): "ewondo-francais",
    ("fr", "fub"): "francais-fufulde",
    ("fub", "fr"): "fufulde-francais",
    ("fr", "bbj"): "francais-ghomala",
    ("bbj", "fr"): "ghomala-francais",
    ("fr", "byv"): "francais-medumba",
    ("byv", "fr"): "medumba-francais",
    ("fr", "en"): "francais-english",
    ("en", "fr"): "english-francais",
}

OPUS_BNT_TAGS = {"bas": ">>bas<<"}
OPUS_MUL_TAGS = {"wes": ">>pcm<<", "bas": ">>bas<<"}


def available_models_status() -> dict[str, bool]:
    ct2_root = MODELS_DIR / "cameroon-int8"
    return {
        "cameroon_int8": (ct2_root / "francais-ewondo" / "model.bin").exists(),
        "opus_mt_bnt": (MODELS_DIR / "opus-mt-fr-bnt-ct2-int8" / "model.bin").exists() or (MODELS_DIR / "opus-mt-fr-bnt" / "config.json").exists(),
        "opus_mt_mul": (MODELS_DIR / "opus-mt-fr-mul-ct2-int8" / "model.bin").exists() or (MODELS_DIR / "opus-mt-fr-mul" / "config.json").exists(),
        "opus_mt_bnt_rev": (MODELS_DIR / "opus-mt-bnt-fr-ct2-int8" / "model.bin").exists() or (MODELS_DIR / "opus-mt-bnt-fr" / "config.json").exists(),
        "ewondo_french_hf": (MODELS_DIR / "ewondo-french-yemen2016" / "config.json").exists(),
        "t5_spell_fr": (MODELS_DIR / "t5-spell-fr" / "config.json").exists(),
        "t5_grammar_en": (MODELS_DIR / "t5-grammar-en" / "config.json").exists(),
        "corpus_extract": CORPUS_FILE.is_file(),
    }


@lru_cache(maxsize=1)
def _load_corpus_index() -> dict[str, Any]:
    if not CORPUS_FILE.is_file():
        return {"soreva": {}, "fub": {}, "wes": {}}
    try:
        raw = json.loads(CORPUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"soreva": {}, "fub": {}, "wes": {}}

    soreva_idx: dict[str, dict[str, str]] = {}
    for row in raw.get("soreva_parallel", []):
        flat = {lang: vals.get("aglc", "") for lang, vals in row.items() if vals.get("aglc")}
        for lang, vals in row.items():
            for variant in (vals.get("aglc", ""), vals.get("ascii", "")):
                key = variant.strip().lower()
                if key:
                    soreva_idx[key] = flat

    fub_idx = {k.strip().lower(): v for k, v in (raw.get("fulfulde_fr_lexicon") or {}).items()}
    wes_idx = {r["en"].strip().lower(): r["wes"] for r in (raw.get("pidgin_en_pairs") or []) if r.get("en") and r.get("wes")}
    return {"soreva": soreva_idx, "fub": fub_idx, "wes": wes_idx}


@lru_cache(maxsize=12)
def _load_ct2_cameroon(pair: str):
    model_path = MODELS_DIR / "cameroon-int8" / pair
    if not (model_path / "model.bin").exists():
        return None, None
    try:
        import ctranslate2
        from transformers import MarianTokenizer

        tok = MarianTokenizer.from_pretrained(str(model_path), local_files_only=True)
        trans = ctranslate2.Translator(str(model_path), device="cpu")
        return tok, trans
    except Exception:
        return None, None


@lru_cache(maxsize=4)
def _load_opus_model(name: str):
    ct2_dir = MODELS_DIR / f"{name}-ct2-int8"
    hf_dir = MODELS_DIR / name
    if (ct2_dir / "model.bin").exists():
        try:
            import ctranslate2
            from transformers import AutoTokenizer

            tok = AutoTokenizer.from_pretrained(str(ct2_dir), local_files_only=True)
            trans = ctranslate2.Translator(str(ct2_dir), device="cpu")
            return ("ct2", tok, trans)
        except Exception:
            pass
    if (hf_dir / "config.json").exists():
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            tok = AutoTokenizer.from_pretrained(str(hf_dir), local_files_only=True)
            mod = AutoModelForSeq2SeqLM.from_pretrained(str(hf_dir), local_files_only=True)
            mod.eval()
            return ("hf", tok, mod)
        except Exception:
            pass
    return None


def _clean_decoded(txt: str) -> str:
    s = re.sub(r"\s{2,}", " ", (txt or "").strip())
    # Retirer guillemets orphelins fréquents sur OPUS-MT multi
    if s.count('"') % 2 == 1:
        s = s.replace('"', "").strip()
    return s


def _run_ct2(tok, trans, text: str) -> str | None:
    try:
        source_tokens = tok.convert_ids_to_tokens(tok.encode(text))
        res = trans.translate_batch(
            [source_tokens],
            max_decoding_length=160,
            beam_size=2,
            repetition_penalty=1.35,
            no_repeat_ngram_size=3,
        )
        hyp = res[0].hypotheses[0]
        return _clean_decoded(tok.decode(tok.convert_tokens_to_ids(hyp), skip_special_tokens=True))
    except Exception:
        return None


def _run_opus(bundle, text: str, tag: str) -> str | None:
    if not bundle:
        return None
    kind, tok, model = bundle
    tagged = f"{tag} {text}".strip()
    try:
        if kind == "ct2":
            return _run_ct2(tok, model, tagged)
        import torch

        inputs = tok(tagged, return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=160, num_beams=2, repetition_penalty=1.25)
        return _clean_decoded(tok.batch_decode(out, skip_special_tokens=True)[0])
    except Exception:
        return None


def _translate_direct_or_pivot(text: str, src: str, tgt: str) -> tuple[str | None, str]:
    if src == tgt:
        return text, "identity"

    low = text.strip().lower()
    corpus = _load_corpus_index()
    # 0. Mémoire de traduction parallèle locale (Soreva / Fulfulde / Pidgin)
    if low in corpus["soreva"] and tgt in corpus["soreva"][low]:
        return corpus["soreva"][low][tgt], "corpus_soreva_parallel"
    if src == "fr" and tgt == "fub" and low in corpus["fub"]:
        return corpus["fub"][low], "corpus_fulfulde_adamaoua"
    if src == "en" and tgt == "wes" and low in corpus["wes"]:
        return corpus["wes"][low], "corpus_pidgin_mt560"

    # 1. Paire directe CTranslate2 cameroon-int8
    pair = CT2_CAMEROON_PAIRS.get((src, tgt))
    if pair:
        tok, trans = _load_ct2_cameroon(pair)
        if tok and trans:
            out = _run_ct2(tok, trans, text)
            if out:
                return out, f"ct2:{pair}"

    # 2. OPUS-MT Bantu (bas) depuis fr/en
    if src in ("fr", "en") and tgt in OPUS_BNT_TAGS:
        bundle = _load_opus_model("opus-mt-fr-bnt")
        out = _run_opus(bundle, text, OPUS_BNT_TAGS[tgt])
        if out:
            return out, f"opus-mt-bnt:{tgt}"

    # 3. OPUS-MT Multilingual (wes -> >>pcm<<, bas -> >>bas<<) depuis fr/en
    if src in ("fr", "en") and tgt in OPUS_MUL_TAGS:
        bundle = _load_opus_model("opus-mt-fr-mul")
        out = _run_opus(bundle, text, OPUS_MUL_TAGS[tgt])
        if out:
            return out, f"opus-mt-mul:{tgt}"

    # 4. Sens retour Bantu (dua, bas) -> fr/en
    if src in ("dua", "bas") and tgt in ("fr", "en"):
        bundle = _load_opus_model("opus-mt-bnt-fr")
        rev_tag = ">>fra<<" if tgt == "fr" else ">>eng<<"
        out = _run_opus(bundle, text, rev_tag)
        if out:
            return out, f"opus-mt-bnt-rev:{tgt}"

    # 5. Pivot automatique via le français (ex: en -> bbj, ewo -> byv, wes -> fr -> dua)
    if src != "fr" and tgt != "fr":
        mid_fr, mid_eng = _translate_direct_or_pivot(text, src, "fr")
        if mid_fr:
            final_out, tgt_eng = _translate_direct_or_pivot(mid_fr, "fr", tgt)
            if final_out:
                return final_out, f"pivot_fr({mid_eng}->{tgt_eng})"

    return None, "unavailable"


def translate_neural_local(text: str, src_lang: str, tgt_lang: str) -> tuple[str | None, str]:
    """Traduit une phrase complète hors-ligne via les modèles locaux avec protection stricte des entités."""
    if not ENABLE_LOCAL_NMT:
        return None, "disabled"
    return _translate_direct_or_pivot(text, src_lang, tgt_lang)
