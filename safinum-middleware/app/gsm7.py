"""Moteur GSM-7 : comptage exact en septets, translittération des langues camerounaises et respect strict des limites par canal."""
import unicodedata

# Jeu de caractères de base GSM 03.38 (1 septet chacun)
GSM7_BASIC = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)

# Table d'extension GSM 03.38 (2 septets chacun : ESC + code)
GSM7_EXTENDED = set("^{}\\[~]|€")

# Table de translittération pour préserver la lisibilité tout en restant 100% GSM-7
TRANSLIT_MAP = {
    # Caractères des langues nationales camerounaises (Alphabet général des langues camerounaises)
    "ɛ": "e", "Ɛ": "E",
    "ɔ": "o", "Ɔ": "O",
    "ŋ": "ng", "Ŋ": "Ng",
    "ə": "e", "Ə": "E",
    "ɓ": "b", "Ɓ": "B",
    "ɗ": "d", "Ɗ": "D",
    "ƙ": "k", "Ƙ": "K",
    "ƴ": "y", "Ƴ": "Y",
    "ɑ": "a", "Ɑ": "A",
    "ɨ": "i", "Ɨ": "I",
    "ʉ": "u", "Ʉ": "U",
    "œ": "oe", "Œ": "OE",
    "ʼ": "'", "ꞌ": "'",
    # Accents français et tons africains non présents dans GSM-7
    "á": "a", "à": "a", "â": "a", "ä": "a", "ã": "a", "ǎ": "a", "ā": "a",
    "Á": "A", "À": "A", "Â": "A", "Ä": "A", "Ã": "A", "Ǎ": "A", "Ā": "A",
    "é": "e", "ê": "e", "ë": "e", "ě": "e", "ē": "e",
    "É": "E", "Ê": "E", "Ë": "E", "Ě": "E", "Ē": "E",
    "í": "i", "î": "i", "ï": "i", "ǐ": "i", "ī": "i",
    "Í": "I", "Î": "I", "Ï": "I", "Ǐ": "I", "Ī": "I",
    "ó": "o", "ô": "o", "ö": "o", "õ": "o", "ǒ": "o", "ō": "o",
    "Ó": "O", "Ô": "O", "Ö": "O", "Õ": "O", "Ǒ": "O", "Ō": "O",
    "ú": "u", "û": "u", "ǔ": "u", "ū": "u",
    "Ú": "U", "Û": "U", "Ǔ": "U", "Ū": "U",
    "ç": "c", "Ç": "C",
    # Ponctuation typographique -> ASCII GSM-7
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "«": '"', "»": '"',
    "—": "-", "–": "-", "−": "-",
    "…": "...",
    "\u00a0": " ", "\u202f": " ", "\u200b": "",
    "•": "-", "·": ".",
}


def septet_length(text: str) -> int:
    """Calcule la longueur exacte en septets GSM-7 (les caractères étendus comptent pour 2)."""
    total = 0
    for ch in text:
        if ch in GSM7_EXTENDED:
            total += 2
        else:
            total += 1
    return total


def is_gsm7(text: str) -> bool:
    """Vérifie si tous les caractères appartiennent au jeu GSM-7 (base ou étendu)."""
    return all(ch in GSM7_BASIC or ch in GSM7_EXTENDED for ch in text)


def transliterate_to_gsm7(text: str) -> str:
    """Convertit un texte multilingue (Ewondo, Fulfulde, Duala, Basaa, Ghomala, Medumba, FR) en GSM-7 strict."""
    # Décomposer NFC puis remplacer les diacritiques combinants non mappés
    normalized = unicodedata.normalize("NFC", text)
    out: list[str] = []
    for ch in normalized:
        if ch in GSM7_BASIC or ch in GSM7_EXTENDED:
            out.append(ch)
        elif ch in TRANSLIT_MAP:
            out.append(TRANSLIT_MAP[ch])
        else:
            # Décomposition NFD pour retirer les marques tonales combinantes (ex. á -> a)
            decomposed = unicodedata.normalize("NFD", ch)
            kept = [c for c in decomposed if unicodedata.category(c) != "Mn"]
            candidate = "".join(kept)
            if candidate and all(c in GSM7_BASIC or c in GSM7_EXTENDED for c in candidate):
                out.append(candidate)
            elif candidate in TRANSLIT_MAP:
                out.append(TRANSLIT_MAP[candidate])
            # Sinon caractère ignoré pour garantir 100% GSM-7
    return "".join(out)


def truncate_gsm7(text: str, max_septets: int) -> str:
    """Tronque proprement un texte GSM-7 sans dépasser max_septets."""
    if septet_length(text) <= max_septets:
        return text
    limit = max(0, max_septets - 3)
    acc: list[str] = []
    used = 0
    for ch in text:
        cost = 2 if ch in GSM7_EXTENDED else 1
        if used + cost > limit:
            break
        acc.append(ch)
        used += cost
    result = "".join(acc).rstrip()
    if max_septets >= 3:
        result += "..."
    return result


def fit_channel_constraints(
    text: str,
    channel: str,
    max_chars: int | None = None,
    charset: str | None = None,
) -> tuple[str, dict]:
    """Adapte le texte aux contraintes du canal et retourne les métadonnées de diagnostic."""
    ch = channel.lower()
    effective_charset = (charset or ("gsm7" if ch in ("ussd", "sms") else "utf8")).lower()

    if ch == "ussd":
        limit = max_chars or 182
        clean = transliterate_to_gsm7(text)
        clean = truncate_gsm7(clean, limit)
        septets = septet_length(clean)
        return clean, {
            "charset": "gsm7",
            "is_gsm7": is_gsm7(clean),
            "septets": septets,
            "chars": len(clean),
            "limit": limit,
            "within_limit": septets <= limit,
        }

    if ch == "sms":
        clean = transliterate_to_gsm7(text) if effective_charset == "gsm7" else text
        septets = septet_length(clean) if is_gsm7(clean) else len(clean)
        if is_gsm7(clean):
            segments = 1 if septets <= 160 else (septets + 152) // 153
        else:
            segments = 1 if len(clean) <= 70 else (len(clean) + 66) // 67
        return clean, {
            "charset": "gsm7" if is_gsm7(clean) else "ucs2",
            "is_gsm7": is_gsm7(clean),
            "septets": septets,
            "chars": len(clean),
            "sms_segments": segments,
            "within_limit": True,
        }

    # mobile (1000), web (2000), atm, ivr
    default_limit = 1000 if ch == "mobile" else 2000
    limit = max_chars or default_limit
    clean = text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
    return clean, {
        "charset": "utf8",
        "is_gsm7": is_gsm7(clean),
        "septets": septet_length(clean),
        "chars": len(clean),
        "limit": limit,
        "within_limit": len(clean) <= limit,
    }
