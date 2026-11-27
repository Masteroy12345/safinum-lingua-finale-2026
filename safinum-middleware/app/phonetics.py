"""Moteur de conjugaison, phonétique (API/IPA), adaptation vocale Sandbox Web/Mobile et synthèse TTS locale (MMS-TTS)."""
from __future__ import annotations

import io
import os
import re
import unicodedata
import wave
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from .config import settings

ROOT_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = Path(os.getenv("SAFINUM_MODELS_DIR", str(ROOT_DIR / "models")))

GRAMMAR_RULES: dict[str, dict[str, Any]] = {
    "ewo": {
        "name": "Ewondo",
        "family": "Bantoue (Beti)",
        "pronouns": {"1s": "má-/mā-", "2s": "wá-/wā-", "3s": "a-", "1p": "biá-/biē-", "2p": "miá-/miä-", "3p": "ba-"},
        "tense_aspect": {
            "present": "ton haut/moyen sur pronom (ex: mā lôm = j'envoie)",
            "past_recent": "marqueur -dzì-",
            "past_remote": "marqueur -bé / -ngá- (ex: mêngá lôm = j'ai envoyé)",
            "future_near": "auxiliaire mayi / -yi- (ex: mayi lôm = je vais envoyer)",
            "negation": "particule finale kìk / ki (ex: mă bô kík = je ne fais pas)",
        },
        "tts_voice_lang": "fr",
        "mms_tts_dir": "mms-tts-ewo",
    },
    "fub": {
        "name": "Fulfulde",
        "family": "Atlantique (Peul / Adamaoua)",
        "pronouns": {"1s": "mi", "2s": "a", "3s": "o", "1p": "min / en", "2p": "on", "3p": "ɓe"},
        "tense_aspect": {
            "accomplished": "suffixes -ii, -ma, -ke (ex: ceede nelaama = l'argent a été envoyé)",
            "inaccomplished_future": "suffixes -ata, -ete, -ay (ex: mi nelay = j'enverrai)",
            "negation_accomplished": "suffixes -aali / -aani (ex: mi nelaali = je n'ai pas envoyé)",
            "phonology": "alternance consonantique (p/b/mb), implosives ɓ/ɗ, voyelles longues (aa, ee, ii, oo, uu)",
        },
        "tts_voice_lang": "fr",
        "mms_tts_dir": "mms-tts-ful",
    },
    "dua": {
        "name": "Duálá",
        "family": "Bantoue (Sawa)",
        "pronouns": {"1s": "na", "2s": "o", "3s": "e / a", "1p": "di", "2p": "lo", "3p": "bá"},
        "tense_aspect": {
            "present": "particule ma (ex: na ma lóma = j'envoie, o ma lóma = tu envoies)",
            "past": "marqueurs tí / tá selon l'éloignement",
            "future": "particules préverbales prospectives + tons",
            "state_be": "ne (je suis), oe (tu es), 'e (il/elle est)",
        },
        "tts_voice_lang": "fr",
        "mms_tts_dir": "mms-tts-fra",
    },
    "bas": {
        "name": "Ɓasaá",
        "family": "Bantoue",
        "pronouns": {"1s": "me", "2s": "u", "3s": "a", "1p": "di", "2p": "ni", "3p": "ba"},
        "tense_aspect": {
            "present": "préfixe nasal ton haut ŋ́- / ḿ- (ex: u nlémèl = tu envoies)",
            "past_near": "préfixe nasal ton bas ǹ- (ex: me ǹsâl = j'ai travaillé)",
            "past_remote": "marqueur bi",
            "state_be_have": "yé (être), ngwé (avoir)",
        },
        "tts_voice_lang": "fr",
        "mms_tts_dir": "mms-tts-fra",
    },
    "bbj": {
        "name": "Ghɔmálá'",
        "family": "Bantoïde Grassfields (Bamiléké)",
        "pronouns": {"1s": "mə / gə", "2s": "o", "3s": "e", "1p": "pə", "2p": "pɨ", "3p": "wə"},
        "tense_aspect": {
            "tam_system": "particules aspecto-temporelles préverbales (accompli/inaccompli) + tons grammaticaux",
            "extensions": "extensions verbales -ra, -ta",
            "negation": "morphèmes discontinus + modification tonale",
        },
        "tts_voice_lang": "fr",
        "mms_tts_dir": "mms-tts-fra",
    },
    "byv": {
        "name": "Mə̀dûmbà",
        "family": "Bantoïde Grassfields (Bamiléké)",
        "pronouns": {"1s": "mə̀", "2s": "u", "3s": "a", "1p": "bə̀", "2p": "bin", "3p": "bu"},
        "tense_aspect": {
            "tam_system": "marqueurs aspecto-temporels entre sujet et verbe + tons lexicaux/grammaticaux",
            "future": "particule ko / zə",
            "negation": "particule négative + variation tonale sur le radical",
        },
        "tts_voice_lang": "fr",
        "mms_tts_dir": "mms-tts-fra",
    },
    "wes": {
        "name": "Pidgin camerounais (Kamtok)",
        "family": "Créole à base lexicale anglaise",
        "pronouns": {"1s": "ah / a", "2s": "yu", "3s": "i / e", "1p": "wi", "2p": "wuna", "3p": "dem"},
        "tense_aspect": {
            "past": "marqueur préverbal bin / bi (ex: ah bin send = j'avais envoyé)",
            "perfect": "marqueur don (ex: moni don go = l'argent est parti) ; négation: neva / neba",
            "future": "marqueur go (ex: yu go receive = tu recevras)",
            "progressive": "marqueur di (ex: dem di comot = ils retirent)",
        },
        "tts_voice_lang": "en",
        "mms_tts_dir": "mms-tts-pcm",
    },
    "fr": {
        "name": "Français",
        "family": "Indo-européenne (Romane)",
        "pronouns": {"1s": "je", "2s": "tu / vous", "3s": "il / elle"},
        "tense_aspect": {"present": "indicatif présent", "future": "futur proche / simple"},
        "tts_voice_lang": "fr",
        "mms_tts_dir": "mms-tts-fra",
    },
    "en": {
        "name": "English",
        "family": "Indo-European (Germanic)",
        "pronouns": {"1s": "I", "2s": "you", "3s": "he / she"},
        "tense_aspect": {"present": "simple / continuous", "future": "will / going to"},
        "tts_voice_lang": "en",
    },
}

# Règles de conversion orthographe AGLC -> Transcription IPA (API)
_IPA_RULES: list[tuple[str, str]] = [
    ("kp", "k͡p"), ("gb", "g͡b"), ("ny", "ɲ"), ("ng", "ŋg"), ("nj", "ⁿdʒ"),
    ("mb", "ᵐb"), ("nd", "ⁿd"), ("sh", "ʃ"), ("ch", "tʃ"), ("ɛ", "ɛ"), ("ɔ", "ɔ"),
    ("ŋ", "ŋ"), ("ə", "ə"), ("ʉ", "ʉ"), ("ɓ", "ɓ"), ("ɗ", "ɗ"), ("ƴ", "j̰"),
    ("ʼ", "ʔ"), ("'", "ʔ"), ("j", "dʒ"), ("y", "j"), ("u", "u"),
]

# Règles phonétiques pour le lecteur vocal Web/Mobile (fr-FR Google SpeechSynthesis)
_UI_WEB_PHONETIC_REPLACEMENTS: list[tuple[str, str]] = [
    ("ɛ", "è"), ("Ɛ", "È"),
    ("ɔ", "o"), ("Ɔ", "O"),
    ("ɑ", "a"), ("Ɑ", "A"),
    ("ŋk", "nk"), ("Ŋk", "Nk"),
    ("ŋ", "ng"), ("Ŋ", "Ng"),
    ("ə", "e"), ("Ə", "E"),
    ("ʉ", "ou"), ("Ʉ", "Ou"),
    ("ɓ", "b"), ("Ɓ", "B"),
    ("ɗ", "d"), ("Ɗ", "D"),
    ("ƴ", "y"), ("Ƴ", "Y"),
    ("ʼ", "'"),
]

# Règles phonétiques étendues pour lecture syllabe par syllabe fluide (voix fr-FR)
_TTS_FR_RULES: list[tuple[str, str]] = [
    ("ɛ", "è"), ("Ɛ", "È"),
    ("ɔ", "o"), ("Ɔ", "O"),
    ("ɑ", "a"), ("Ɑ", "A"),
    ("ŋk", "nk"), ("Ŋk", "Nk"),
    ("ŋg", "ng"), ("Ŋg", "Ng"),
    ("ŋ", "ng"), ("Ŋ", "Ng"),
    ("ə", "e"), ("Ə", "E"),
    ("ʉ", "ou"), ("Ʉ", "Ou"),
    ("ɓ", "b"), ("Ɓ", "B"),
    ("ɗ", "d"), ("Ɗ", "D"),
    ("ƴ", "y"), ("Ƴ", "Y"),
    ("ny", "gn"), ("Ny", "Gn"),
    ("ch", "tch"), ("Ch", "Tch"),
    ("sh", "ch"), ("Sh", "Ch"),
    ("ʼ", ""), ("'", " "),
]

_FR_ONES = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize"]
_FR_TENS = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante", "quatre-vingt", "quatre-vingt"]


def _int_to_fr_words(n: int) -> str:
    """Convertit un entier en toutes lettres en français pour que MMS-TTS lise les montants en syllabes."""
    if n == 0:
        return "zéro"
    if n < 0:
        return "moins " + _int_to_fr_words(-n)
    parts: list[str] = []
    if n >= 1_000_000:
        m = n // 1_000_000
        parts.append(("un million" if m == 1 else f"{_int_to_fr_words(m)} millions"))
        n %= 1_000_000
    if n >= 1000:
        k = n // 1000
        parts.append("mille" if k == 1 else f"{_int_to_fr_words(k)} mille")
        n %= 1000
    if n >= 100:
        c = n // 100
        parts.append("cent" if c == 1 else f"{_FR_ONES[c]} cent")
        n %= 100
    if n > 0:
        if n <= 16:
            parts.append(_FR_ONES[n])
        elif n < 20:
            parts.append(f"dix-{_FR_ONES[n - 10]}")
        else:
            t, u = n // 10, n % 10
            if t in (7, 9):
                sub = 10 + u
                sep = " et " if (t == 7 and u == 1) else "-"
                parts.append(f"{_FR_TENS[t]}{sep}{_int_to_fr_words(sub)}")
            else:
                if u == 0:
                    parts.append(_FR_TENS[t])
                elif u == 1 and t != 8:
                    parts.append(f"{_FR_TENS[t]} et un")
                else:
                    parts.append(f"{_FR_TENS[t]}-{_FR_ONES[u]}")
    return " ".join(parts)


def _expand_numbers_for_tts(text: str) -> str:
    """Transforme les montants (15 000 -> quinze mille) et numéros (677000002) en mots prononçables en syllabes."""
    # 1. Numéros de téléphone camerounais (9 ou 12 chiffres) -> lus par paires/chiffres en mots
    def _phone_to_words(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        return " ".join(_FR_ONES[int(d)] for d in digits)

    out = re.sub(r"(?:\+?237[\s\-\.]?)?[26](?:[\s\-\.]?\d){8}\b", _phone_to_words, text)

    # 2. Montants formatés avec espaces (ex: "15 000", "250 000", "5000")
    def _num_to_words(m: re.Match) -> str:
        raw_digits = re.sub(r"[\s\.,]", "", m.group(0))
        if not raw_digits.isdigit():
            return m.group(0)
        val = int(raw_digits)
        if val <= 999_999_999:
            return _int_to_fr_words(val)
        return " ".join(_FR_ONES[int(d)] for d in raw_digits)

    out = re.sub(r"\b\d{1,3}(?:[\s\.]\d{3})+\b|\b\d+\b", _num_to_words, out)
    return out

_PROTECTED_MULTI_NAME_RE = re.compile(
    r"\{[a-z_]+\}|"
    r"(?:TRX|SAF)-[A-Za-z0-9\-]+|"
    r"(?:\+?237[\s\-\.]?)?[26](?:[\s\-\.]?\d){8}\b|"
    r"\b\d[\d\s\.,]*\s*(?:FCFA|XAF|CFA)\b|"
    r"\b(?:FCFA|XAF|CFA|ENEO|CAMWATER|CANAL\+?|CAMTEL|MTN|ORANGE|Safinum(?:\s+Pay)?)\b|"
    r"\b\d+(?:[\s\.,]\d+)*\b|"
    r"\b[A-ZÀ-Ÿ][a-zà-ÿ'\-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ'\-]+)+\b"
)
_PREP_SINGLE_NAME_RE = re.compile(
    r"(\b(?:[àa]|pour|de|vers|chez|give|to|from|na|o|i|e|[Bb]onjour|[Hh]ello|[Mm]bolo|[Ss]annu|[Ii]dib'a|[Kk]ɛl)\s+)([A-ZÀ-Ÿ][a-zà-ÿ'\-]+)\b"
)


def _find_protected_spans(text: str) -> list[tuple[int, int]]:
    """Identifie les plages (start, end) protégées : montants, numéros, FCFA, noms propres simples et composés."""
    spans: list[tuple[int, int]] = [m.span() for m in _PROTECTED_MULTI_NAME_RE.finditer(text)]
    for m in _PREP_SINGLE_NAME_RE.finditer(text):
        ns, ne = m.span(2)
        if not any(s <= ns and ne <= e for s, e in spans):
            spans.append((ns, ne))
    spans.sort()
    # Fusionner les plages qui se chevauchent
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _apply_outside_protected(text: str, fn) -> str:
    spans = _find_protected_spans(text)
    if not spans:
        return fn(text)
    out: list[str] = []
    pos = 0
    for s, e in spans:
        if pos < s:
            out.append(fn(text[pos:s]))
        out.append(text[s:e])
        pos = e
    if pos < len(text):
        out.append(fn(text[pos:]))
    return "".join(out)


def to_ipa(text: str, lang: str = "fr") -> str:
    """Produit une transcription phonétique IPA (API) normalisée en protégeant nombres et emplacements."""
    def _conv(seg: str) -> str:
        t = unicodedata.normalize("NFC", seg).lower()
        for src, dst in _IPA_RULES:
            t = t.replace(src, dst)
        return t

    body = _apply_outside_protected(text, _conv)
    return f"/{body}/"


def to_web_phonetic_safe(text: str, lang: str = "fr") -> str:
    """Rend un texte d'interface Mobile/Web lisible ET bien prononcé par la synthèse vocale fr-FR du sandbox.

    Remplace les symboles AGLC/API non reconnus par Google français (`ɛ, ɔ, ŋ, ə, ɓ, ɗ, ʉ`) par
    leurs équivalents orthographiques phonétiques naturels (`è, o, ng/nk, e, b, d, ou`) et retire les
    diacritiques combinants rares qui coupent la lecture vocale, tout en préservant les emplacements `{...}`.
    """
    if lang in ("fr", "en"):
        return text

    def _conv(seg: str) -> str:
        t = unicodedata.normalize("NFC", seg)
        for src, dst in _UI_WEB_PHONETIC_REPLACEMENTS:
            t = t.replace(src, dst)
        # Retirer les tons rares combinants (caron, macron, etc.) mais garder é/è/à/ô/ê/û
        nfd = unicodedata.normalize("NFD", t)
        kept = [c for c in nfd if unicodedata.category(c) != "Mn" or c in {"\u0301", "\u0300", "\u0302"}]
        res = unicodedata.normalize("NFC", "".join(kept))
        # En langues camerounaises, 'u' isolé ou suivi de consonne se prononce /u/ ('ou') et non /y/ ('u' français)
        # On convertit certains mots-clés usuels si besoin sans casser la lisibilité
        if lang != "wes":
            res = re.sub(r"\b([Ss])annu\b", r"\1annou", res)
            res = re.sub(r"\b([Mm])bu\b", r"\1bou", res)
            res = re.sub(r"\b([Nn])tum\b", r"\1toum", res)
            res = re.sub(r"\b([Ff])uu\b", r"\1ou", res)
        return res

    return _apply_outside_protected(text, _conv)


def to_tts_script(text: str, lang: str = "fr") -> str:
    """Transforme un texte en script phonétique fluide lu syllabe par syllabe (noms propres, chiffres bruts et FCFA lus en français)."""
    t = unicodedata.normalize("NFC", text)
    if lang == "wes":
        def _wes(seg: str) -> str:
            s = re.sub(r"\bmoni\b", "money", seg, flags=re.IGNORECASE)
            s = re.sub(r"\bpesin\b", "person", s, flags=re.IGNORECASE)
            s = re.sub(r"\bweh\b", "way", s, flags=re.IGNORECASE)
            s = re.sub(r"\bfo\b", "for", s, flags=re.IGNORECASE)
            s = re.sub(r"\byu\b", "you", s, flags=re.IGNORECASE)
            s = re.sub(r"\babeg\b", "a beg", s, flags=re.IGNORECASE)
            s = re.sub(r"\bwuna\b", "wouna", s, flags=re.IGNORECASE)
            s = re.sub(r"\bwetin\b", "wétin", s, flags=re.IGNORECASE)
            return s
        res = _apply_outside_protected(t, _wes)
    elif lang in ("en", "fr"):
        res = t
    else:
        def _fr_phon(seg: str) -> str:
            s = unicodedata.normalize("NFC", seg)
            for src, dst in _TTS_FR_RULES:
                s = s.replace(src, dst)
            # 'ee' -> 'é', 'aa' -> 'a', 'ii' -> 'i', 'oo' -> 'o', 'uu' -> 'ou'
            s = re.sub(r"ee+", "é", s, flags=re.IGNORECASE)
            s = re.sub(r"uu+", "ou", s, flags=re.IGNORECASE)
            s = re.sub(r"([aioAIO])\1+", r"\1", s)
            # 'u' isolé en orthographe camerounaise = /u/ ('ou')
            s = re.sub(r"(?<![aeouAEOU])u", "ou", s)
            s = re.sub(r"(?<![aeouAEOU])U", "Ou", s)
            # Groupes consonantiques initiaux africains sans voyelle d'appui -> 'e' muet léger pour lecture syllabique
            s = re.sub(r"\b([MmNn])([bpdtkgcsz])", r"\1e\2", s)
            nfd = unicodedata.normalize("NFD", s)
            cleaned = "".join(c for c in nfd if unicodedata.category(c) != "Mn" or c in {"\u0301", "\u0300", "\u0302"})
            return unicodedata.normalize("NFC", cleaned)

        res = _apply_outside_protected(t, _fr_phon)
        # Nettoyer les apostrophes internes hors noms propres pour éviter l'épellation
        res = _apply_outside_protected(res, lambda seg: re.sub(r"['ʼ`]", " ", seg))

    # Décomposition dynamique de tout numéro de téléphone variable avant lecture TTS
    res = _format_phones_for_natural_audio(res)
    # Sigles/devises prononcés en français sans traduire FCFA dans l'écrit
    res = re.sub(r"\bFCFA\b", "francs céfa", res, flags=re.IGNORECASE)
    res = re.sub(r"\bXAF\b", "francs céfa", res, flags=re.IGNORECASE)
    res = re.sub(r"\bCFA\b", "céfa", res, flags=re.IGNORECASE)
    res = re.sub(r"\bENEO\b", "énéo", res, flags=re.IGNORECASE)
    res = re.sub(r"\bCAMWATER\b", "camouateur", res, flags=re.IGNORECASE)
    res = re.sub(r"\bCAMTEL\b", "camtel", res, flags=re.IGNORECASE)
    res = re.sub(r"\bORANGE\b", "orange", res, flags=re.IGNORECASE)
    res = re.sub(r"\bMTN\b", "èm té èn", res, flags=re.IGNORECASE)
    res = re.sub(r"\bTRX-([A-Za-z0-9]+)\b", r"référence \1", res, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", res).strip()


def build_audio_payload(text: str, lang: str) -> dict[str, Any]:
    """Retourne le texte original, la transcription IPA, le texte Web phonétique et le script TTS."""
    rule = GRAMMAR_RULES.get(lang, {})
    tts_lang = rule.get("tts_voice_lang", "en" if lang in ("en", "wes") else "fr")
    has_neural = bool(settings.elevenlabs_api_key) or bool(rule.get("mms_tts_dir") and (MODELS_DIR / str(rule.get("mms_tts_dir"))).is_dir())
    use_eleven = bool((settings.elevenlabs_api_key or "").strip())
    return {
        "language": lang,
        "text": text,
        "web_phonetic": to_web_phonetic_safe(text, lang),
        "ipa": to_ipa(text, lang),
        "tts_script": to_tts_script(text, lang),
        "elevenlabs_native_text": _prepare_elevenlabs_native_text(text, lang) if use_eleven else "",
        "tts_voice_lang": tts_lang,
        "neural_tts_available": has_neural,
        "tts_engine": "elevenlabs-male" if use_eleven else "mms-tts-fra-male",
    }


@lru_cache(maxsize=4)
def _load_mms_tts(model_dir_name: str):
    model_path = MODELS_DIR / model_dir_name
    if not model_path.is_dir():
        return None, None
    try:
        from transformers import AutoTokenizer, VitsModel

        tok = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
        mod = VitsModel.from_pretrained(str(model_path), local_files_only=True)
        return tok, mod
    except Exception:
        return None, None


def _estimate_median_f0(waveform: np.ndarray, sr: int) -> float:
    """Estime la fréquence fondamentale médiane (F0 en Hz) sur les trames voisées."""
    frame_len = 512
    pitches: list[float] = []
    min_lag, max_lag = max(1, int(sr / 350)), max(2, int(sr / 70))
    for i in range(0, len(waveform) - frame_len, frame_len):
        frame = waveform[i : i + frame_len]
        if float(np.sqrt(np.mean(frame**2))) < 0.03:
            continue
        corr = np.correlate(frame, frame, mode="full")[frame_len - 1 :]
        if len(corr) <= max_lag:
            continue
        lag = int(np.argmax(corr[min_lag:max_lag]) + min_lag)
        if corr[lag] > 0.3 * corr[0]:
            pitches.append(float(sr) / lag)
    return float(np.median(pitches)) if pitches else 120.0


def _ensure_male_timbre(waveform: np.ndarray, sr: int) -> np.ndarray:
    """Garantit une voix 100% masculine (~120 Hz) en supprimant tout timbre féminin (> 150 Hz)."""
    f0 = _estimate_median_f0(waveform, sr)
    if f0 <= 148.0:
        return waveform
    # Conversion vers timbre masculin naturel (~120 Hz) + maintien du débit via ffmpeg
    target_f0 = 122.0
    ratio = target_f0 / min(f0, 260.0)  # ex: 122 / 225 = 0.542
    tempo = min(1.85, max(1.0, 1.0 / ratio))
    try:
        import subprocess

        max_v = float(np.max(np.abs(waveform))) or 1.0
        pcm_in = np.int16((waveform / max_v) * 32767.0).tobytes()
        shifted_rate = max(8000, int(round(sr * ratio)))
        af_filter = f"asetrate={shifted_rate},aresample={sr},atempo={tempo:.3f},lowpass=f=3800"
        out_bytes = subprocess.check_output(
            [
                "ffmpeg", "-v", "error",
                "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
                "-af", af_filter,
                "-f", "s16le", "-ar", str(sr), "-ac", "1", "pipe:1",
            ],
            input=pcm_in,
        )
        return np.frombuffer(out_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    except Exception:
        # Repli numpy : abaissement direct de la hauteur tonale
        idx = np.arange(0, len(waveform), ratio)
        idx = idx[idx < len(waveform) - 1]
        return np.interp(idx, np.arange(len(waveform)), waveform).astype(np.float32)


_ELEVENLABS_WAV_CACHE: OrderedDict[tuple[str, str, str, str], bytes] = OrderedDict()
_ELEVENLABS_CACHE_MAX = 96


def _speak_phone_pair(pair: str) -> str:
    """Prononce fidèlement chaque bloc de 2 chiffres sans avaler les zéros initiaux (00 -> zéro zéro, 09 -> zéro 9, 77 -> 77)."""
    if len(pair) == 2 and pair[0] == "0":
        return "zéro zéro" if pair == "00" else f"zéro {pair[1]}"
    return pair


def _format_phones_for_natural_audio(text: str) -> str:
    """Récupère et décompose dynamiquement N'IMPORTE QUEL numéro de téléphone (variable) en blocs naturels camerounais.

    Exemples :
    - 237657096450 -> 237, 6, 57, zéro 9, 64, 50
    - +237 6 77 00 00 02 -> +237, 6, 77, zéro zéro, zéro zéro, zéro 2
    - 699050041 -> 6, 99, zéro 5, zéro zéro, 41
    """
    def _fmt(m: re.Match) -> str:
        raw = m.group(0)
        has_plus = raw.lstrip().startswith("+")
        digits = re.sub(r"\D", "", raw)
        prefix = ""
        if digits.startswith("00237") and len(digits) == 14:
            prefix = "+237, "
            digits = digits[5:]
        elif digits.startswith("237") and len(digits) == 12:
            prefix = "+237, " if has_plus else "237, "
            digits = digits[3:]
        if len(digits) == 9:
            blocks = [digits[0], digits[1:3], digits[3:5], digits[5:7], digits[7:9]]
            spoken = [blocks[0]] + [_speak_phone_pair(b) for b in blocks[1:]]
            return prefix + ", ".join(spoken)
        # Repli générique pour tout autre numéro long (8-15 chiffres) : paires de 2 chiffres
        if 8 <= len(digits) <= 15:
            pairs = [digits[i:i + 2] for i in range(0, len(digits), 2)]
            return (("+ " if has_plus else "") + ", ".join(_speak_phone_pair(p) for p in pairs)).strip()
        return raw

    return re.sub(r"(?:(?:\+|00)237[\s\-\.]?|237[\s\-\.]?)?[26](?:[\s\-\.]?\d){8}\b", _fmt, text)


def _prepare_elevenlabs_native_text(text: str, lang: str = "fr") -> str:
    """Prépare le texte natif pour une lecture UNIQUE ElevenLabs en copiant la tonalité du dataset SOREVA.

    - Applique les tons et voyelles natives extraits de SOREVA (sans toucher aux noms propres, chiffres ni FCFA).
    - Formate les numéros de téléphone en blocs naturels (6, 77, 00, 00, 02) afin qu'ils soient lus normalement sans traduction.
    - Aucun découpage ni mélange de deux fichiers audio : génère un seul texte fluide lu d'une seule traite.
    """
    t = unicodedata.normalize("NFC", text or "").strip()
    if not t:
        return ""
    try:
        from .native_voice_bank import apply_native_tonality

        t = _apply_outside_protected(t, lambda seg: apply_native_tonality(seg, lang))
    except Exception:
        pass
    t = _format_phones_for_natural_audio(t)
    t = re.sub(r"\bFCFA\b", "francs CFA", t, flags=re.IGNORECASE)
    t = re.sub(r"\bXAF\b", "francs CFA", t, flags=re.IGNORECASE)
    t = re.sub(r"\bTRX-([A-Za-z0-9]+)\b", r"référence \1", t, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", t).strip()


def _synthesize_elevenlabs_wav(native_text: str, lang: str = "fr") -> bytes | None:
    """Synthèse studio unique via ElevenLabs avec tonalité et prosodie calibrées sur le dataset SOREVA."""
    api_key = (settings.elevenlabs_api_key or "").strip()
    if not api_key or not native_text.strip():
        return None
    voice_id = (settings.elevenlabs_voice_id or "nPczCjzI2devNBz1zQrb").strip()
    model_id = (settings.elevenlabs_model_id or "eleven_multilingual_v2").strip()
    # "fr" garantit que les chiffres bruts, noms propres et "francs CFA" sont lus en français même au milieu d'une phrase camerounaise
    lang_code = "fr" if lang != "en" else "en"
    cache_key = (native_text, voice_id, model_id, lang_code)
    cached = _ELEVENLABS_WAV_CACHE.get(cache_key)
    if cached is not None:
        _ELEVENLABS_WAV_CACHE.move_to_end(cache_key)
        return cached

    try:
        from .native_voice_bank import get_language_voice_settings

        voice_settings = get_language_voice_settings(lang)
    except Exception:
        voice_settings = {
            "stability": 0.55,
            "similarity_boost": 0.78,
            "style": 0.12,
            "use_speaker_boost": True,
        }

    try:
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_24000",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={
                "text": native_text,
                "model_id": model_id,
                "language_code": lang_code,
                "voice_settings": voice_settings,
            },
            timeout=15.0,
        )
        if resp.status_code != 200 or len(resp.content) < 64:
            return None

        raw = resp.content[: len(resp.content) - (len(resp.content) % 2)]
        waveform = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        sr = 24000
        waveform = _ensure_male_timbre(waveform, sr)
        max_val = float(np.max(np.abs(waveform))) or 1.0
        pcm = np.int16(np.clip(waveform / max_val, -1.0, 1.0) * 32767.0)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm.tobytes())
        wav_bytes = buf.getvalue()

        _ELEVENLABS_WAV_CACHE[cache_key] = wav_bytes
        if len(_ELEVENLABS_WAV_CACHE) > _ELEVENLABS_CACHE_MAX:
            _ELEVENLABS_WAV_CACHE.popitem(last=False)
        return wav_bytes
    except Exception:
        return None


def synthesize_wav_bytes(text: str, lang: str) -> tuple[bytes | None, str]:
    """Génère UN SEUL flux audio WAV unifié via ElevenLabs en transférant la tonalité native SOREVA.

    - Aucun mélange de deux audios ni lecture des clips bruts du dataset : la tonalité et les accents SOREVA
      sont injectés dans le texte et les paramètres prosodiques d'ElevenLabs pour une lecture unique et homogène.
    - Noms propres, chiffres bruts et 'francs CFA' sont lus en français dans le même flux vocal masculin.
    """
    # 1. Lecture unifiée ElevenLabs enrichie de la tonalité et de la prosodie natives SOREVA
    native_text = _prepare_elevenlabs_native_text(text, lang)
    eleven_wav = _synthesize_elevenlabs_wav(native_text, lang)
    if eleven_wav:
        return eleven_wav, "elevenlabs-brian-male"

    # 2. Repli 100% hors-ligne : MMS-TTS français calibré en timbre masculin
    spoken = _expand_numbers_for_tts(to_tts_script(text, lang))
    model_dir = "mms-tts-fra"
    tok, mod = _load_mms_tts(model_dir)
    if not tok or not mod:
        return None, "model_not_downloaded"

    try:
        import torch

        # Normaliser en minuscules (le tokenizer MMS-TTS n'a que des lettres minuscules ; les majuscules tombaient en <unk> et hachaient les mots)
        vocab = tok.get_vocab()
        lowered = unicodedata.normalize("NFC", spoken).lower()
        # Remplacer la ponctuation par des espaces simples et filtrer uniquement les caractères supportés par le modèle
        cleaned_chars: list[str] = []
        for ch in lowered:
            if ch in vocab:
                cleaned_chars.append(ch)
            elif ch in {",", ".", ";", ":", "!", "?", "(", ")", "[", "]", "/", "\\", '"', "’", "'"}:
                cleaned_chars.append(" ")
            else:
                # Si caractère accentué non présent dans ce vocabulaire précis, replier sur sa lettre de base
                base = "".join(c for c in unicodedata.normalize("NFD", ch) if unicodedata.category(c) != "Mn")
                if base and base in vocab:
                    cleaned_chars.append(base)
                else:
                    cleaned_chars.append(" ")
        clean = re.sub(r"\s{2,}", " ", "".join(cleaned_chars)).strip()
        if not clean:
            clean = "bonjour"

        inputs = tok(clean, return_tensors="pt")
        with torch.no_grad():
            waveform = mod(**inputs).waveform[0].cpu().numpy()
        sr = int(getattr(mod.config, "sampling_rate", 16000))
        waveform = _ensure_male_timbre(waveform, sr)
        # Normaliser en PCM 16-bit WAV
        max_val = float(np.max(np.abs(waveform))) or 1.0
        pcm = np.int16((waveform / max_val) * 32767.0)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue(), f"{model_dir}-male"
    except Exception as exc:
        return None, f"tts_error:{exc}"
