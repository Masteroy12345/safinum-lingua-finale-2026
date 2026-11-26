"""Moteur de conjugaison, phonétique (API/IPA), adaptation vocale Sandbox Web/Mobile et synthèse TTS locale (MMS-TTS)."""
from __future__ import annotations

import io
import os
import re
import unicodedata
import wave
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

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

# Règles phonétiques étendues pour script TTS pur (prononciation exacte par voix fr-FR)
_TTS_FR_RULES: list[tuple[str, str]] = [
    ("ɛ", "è"), ("Ɛ", "È"),
    ("ɔ", "o"), ("Ɔ", "O"),
    ("ɑ", "a"), ("Ɑ", "A"),
    ("ŋk", "n'k"), ("Ŋk", "N'k"),
    ("ŋ", "ng"), ("Ŋ", "Ng"),
    ("ə", "eu"), ("Ə", "Eu"),
    ("ʉ", "ou"), ("Ʉ", "Ou"),
    ("ɓ", "b"), ("Ɓ", "B"),
    ("ɗ", "d"), ("Ɗ", "D"),
    ("ƴ", "y"), ("Ƴ", "Y"),
    ("ny", "gn"), ("Ny", "Gn"),
    ("ch", "tch"), ("Ch", "Tch"),
    ("sh", "ch"), ("Sh", "Ch"),
    ("ʼ", ""),
]

_PROTECTED_RE = re.compile(r"(\{[a-z_]+\}|(?:TRX|SAF)-[A-Z0-9\-]+|\b(?:FCFA|XAF|ENEO|CAMWATER|CANAL|CAMTEL|MTN|ORANGE|Safinum)\b|\d+)")


def _apply_outside_protected(text: str, fn) -> str:
    parts = _PROTECTED_RE.split(text)
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
        else:
            out.append(fn(part))
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
    """Transforme un texte en script phonétique optimisé pour la synthèse vocale (TTS `fr-FR` / `en`)."""
    t = unicodedata.normalize("NFC", text)
    if lang == "wes":
        def _wes(seg: str) -> str:
            s = re.sub(r"\bmoni\b", "money", seg, flags=re.IGNORECASE)
            s = re.sub(r"\bpesin\b", "person", s, flags=re.IGNORECASE)
            s = re.sub(r"\bweh\b", "way", s, flags=re.IGNORECASE)
            s = re.sub(r"\bfo\b", "for", s, flags=re.IGNORECASE)
            s = re.sub(r"\byu\b", "you", s, flags=re.IGNORECASE)
            s = re.sub(r"\babeg\b", "a beg", s, flags=re.IGNORECASE)
            return s
        return _apply_outside_protected(t, _wes).replace("FCFA", "francs C F A")

    if lang == "en":
        return t.replace("FCFA", "francs C F A")

    if lang == "fr":
        return t.replace("FCFA", "francs C F A")

    def _fr_phon(seg: str) -> str:
        s = unicodedata.normalize("NFC", seg)
        for src, dst in _TTS_FR_RULES:
            s = s.replace(src, dst)
        # 'ee' -> 'é', 'aa' -> 'a', 'ii' -> 'i', 'oo' -> 'o', 'uu' -> 'ou'
        s = re.sub(r"ee+", "é", s, flags=re.IGNORECASE)
        s = re.sub(r"uu+", "ou", s, flags=re.IGNORECASE)
        s = re.sub(r"([aioAIO])\1+", r"\1", s)
        # 'u' isolé en orthographe africaine = /u/ ('ou') mais préserver les digrammes FR (eu, ou, au)
        s = re.sub(r"(?<![aeouAEOU])u", "ou", s)
        s = re.sub(r"(?<![aeouAEOU])U", "Ou", s)
        nfd = unicodedata.normalize("NFD", s)
        cleaned = "".join(c for c in nfd if unicodedata.category(c) != "Mn" or c in {"\u0301", "\u0300", "\u0302"})
        return unicodedata.normalize("NFC", cleaned)

    return _apply_outside_protected(t, _fr_phon).replace("FCFA", "francs C F A")


def build_audio_payload(text: str, lang: str) -> dict[str, Any]:
    """Retourne le texte original, la transcription IPA, le texte Web phonétique et le script TTS."""
    rule = GRAMMAR_RULES.get(lang, {})
    tts_lang = rule.get("tts_voice_lang", "en" if lang in ("en", "wes") else "fr")
    has_neural = bool(rule.get("mms_tts_dir") and (MODELS_DIR / str(rule.get("mms_tts_dir"))).is_dir())
    return {
        "language": lang,
        "text": text,
        "web_phonetic": to_web_phonetic_safe(text, lang),
        "ipa": to_ipa(text, lang),
        "tts_script": to_tts_script(text, lang),
        "tts_voice_lang": tts_lang,
        "neural_tts_available": has_neural,
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


def synthesize_wav_bytes(text: str, lang: str) -> tuple[bytes | None, str]:
    """Génère de l'audio WAV local via Meta MMS-TTS (ewo, fub, wes, fr) si le modèle est présent."""
    rule = GRAMMAR_RULES.get(lang, {})
    model_dir = rule.get("mms_tts_dir")
    if not model_dir:
        return None, "no_neural_tts_for_lang"

    tok, mod = _load_mms_tts(model_dir)
    if not tok or not mod:
        return None, "model_not_downloaded"

    try:
        import torch

        clean = text.replace("FCFA", "francs").replace("XAF", "francs")
        inputs = tok(clean, return_tensors="pt")
        with torch.no_grad():
            waveform = mod(**inputs).waveform[0].cpu().numpy()
        # Normaliser en PCM 16-bit WAV
        max_val = float(np.max(np.abs(waveform))) or 1.0
        pcm = np.int16((waveform / max_val) * 32767.0)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(int(getattr(mod.config, "sampling_rate", 16000)))
            wf.writeframes(pcm.tobytes())
        return buf.getvalue(), model_dir
    except Exception as exc:
        return None, f"tts_error:{exc}"
