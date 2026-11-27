"""Moteur NLU hybride multilingue (9 langues) pour SAFINUM Lingua.

Combine :
1. Extraction déterministe ultra-rapide (< 5 ms) pour les 13 intentions standard + entités financières.
2. Repli neuronal local CTranslate2 (cameroon-int8 <lang>-francais) sur requêtes libres inédites.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from .languages import LANGUAGE_ALIASES
from .models import Intent

ROOT_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = Path(os.getenv("SAFINUM_MODELS_DIR", str(ROOT_DIR / "models")))
ENABLE_NMT_NLU = os.getenv("SAFINUM_ENABLE_NMT_NLU", "1") == "1"


@dataclass
class NLUResult:
    intent: Intent
    parameters: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


BILLERS = {"ENEO", "CAMWATER", "CANAL", "CAMTEL"}
OPERATORS = {"MTN", "ORANGE", "CAMTEL"}

TERM_KEYWORDS = {
    "frais": ["frais", "fee", "fees", "charges", "njobdi", "njoɓdi", "kudin aiki", "kuɗin aiki", "fre", "njoa", "nsas", "commission"],
    "solde": ["solde", "balance", "ceede keddiide", "ragowar kudi", "moni wom", "mòni wom", "mòni a lig", "moni a lig", "a lig ma", "moné a li'i", "mone a li'i", "mone ma tabe", "moni ma dia", "moni u nkon", "nkap ya tse", "nkap bwam"],
    "plafond": ["plafond", "limit", "limite", "maximum", "keeri", "iyaka", "ndelo", "ndék", "ndek", "max"],
    "beneficiaire": ["beneficiaire", "bénéficiaire", "beneficiary", "destinataire", "heboowo", "heɓoowo", "mai karba", "môt a nyoñ", "mot a nyon", "mod a kos", "moto nu ma kusa", "mut a nkos", "we e nyam"],
    "reference": ["reference", "référence", "lambar shaida", "referaans", "referans", "recu", "reçu", "receipt"],
}

_CT2_REVERSE_MAP = {
    "ewo": "ewondo-francais",
    "fub": "fufulde-francais",
    "bbj": "ghomala-francais",
    "byv": "medumba-francais",
    "en": "english-francais",
}


@lru_cache(maxsize=6)
def _load_ct2_reverse(pair: str):
    model_path = MODELS_DIR / "cameroon-int8" / pair
    if not model_path.is_dir():
        return None, None
    try:
        import ctranslate2
        from transformers import MarianTokenizer

        tok = MarianTokenizer.from_pretrained(str(model_path), local_files_only=True)
        trans = ctranslate2.Translator(str(model_path), device="cpu")
        return tok, trans
    except Exception:
        return None, None


def _pivot_to_french(text: str, lang: str | None) -> str | None:
    if not ENABLE_NMT_NLU or not lang or lang not in _CT2_REVERSE_MAP:
        return None
    tok, trans = _load_ct2_reverse(_CT2_REVERSE_MAP[lang])
    if not tok or not trans:
        return None
    try:
        tokens = tok.convert_ids_to_tokens(tok.encode(text))
        res = trans.translate_batch([tokens], max_decoding_length=80)
        hyp = res[0].hypotheses[0]
        return tok.decode(tok.convert_tokens_to_ids(hyp), skip_special_tokens=True).strip()
    except Exception:
        return None


def extract_phone(text: str) -> str | None:
    """Extrait un numéro camerounais (+237 6XX..., 2376..., 6XXXXXXXX)."""
    cleaned = re.sub(r"[\s\-\.]", "", text)
    m = re.search(r"(?:\+?237)?(6\d{8})", cleaned)
    if m:
        return f"237{m.group(1)}"
    return None


def extract_amount(text: str) -> int | None:
    """Extrait un montant en FCFA (gère espaces, points, virgules, k, mille)."""
    without_phones = re.sub(r"(?:\+?237[\s\-\.]?)?[26](?:[\s\-\.]?\d){8}\b", " ", text)
    m_k = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:k|mille)\b", without_phones, re.IGNORECASE)
    if m_k:
        val = float(m_k.group(1).replace(",", "."))
        return int(round(val * 1000))
    m = re.search(r"\b(\d{1,3}(?:[\s\.,]\d{3})+|\d+)\b", without_phones)
    if m:
        digits = re.sub(r"[\s\.,]", "", m.group(1))
        val = int(digits)
        if val > 0:
            return val
    return None


def extract_biller_or_operator(text: str) -> tuple[str | None, str | None]:
    upper = text.upper()
    biller = next((b for b in BILLERS if re.search(rf"\b{b}\b", upper)), None)
    operator = next((o for o in OPERATORS if re.search(rf"\b{o}\b", upper)), None)
    return biller, operator


def extract_beneficiary_name(text: str, allow_bare: bool = False) -> str | None:
    """Extrait un nom de bénéficiaire après prépositions ou en réponse directe."""
    patterns = [
        r"(?:\b(?:a|à|vers|pour|to|give|for|na|e|zuwa|be)\b)\s+([A-ZÀ-Ÿa-zà-ÿ][A-ZÀ-Ÿa-zà-ÿ\-']+(?:\s+[A-ZÀ-Ÿa-zà-ÿ][A-ZÀ-Ÿa-zà-ÿ\-']+)?)",
    ]
    stopwords = {
        "fcfa", "xaf", "cfa", "frais", "solde", "moni", "ceede", "mone", "moné", "kudi", "credit",
        "facture", "bill", "airtime", "nkap", "njoa", "nsas", "fre", "mille", "lissafi", "katin",
    }
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if candidate.lower() not in stopwords and not candidate.isdigit() and not extract_phone(candidate):
                return candidate

    if allow_bare:
        clean = text.strip()
        if (
            clean
            and len(clean.split()) <= 3
            and not extract_phone(clean)
            and not extract_amount(clean)
            and clean.lower() not in stopwords
            and re.match(r"^[A-ZÀ-Ÿa-zà-ÿ][A-ZÀ-Ÿa-zà-ÿ\-'\s]+$", clean)
        ):
            return clean
    return None


def extract_target_language(text: str) -> str | None:
    t = text.lower()
    # Priorité aux noms complets et codes ISO 639-3 (>= 3 caractères) pour éviter la collision avec la préposition française "en"
    for alias, code in sorted(LANGUAGE_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
        if len(alias) < 3:
            continue
        if re.search(rf"\b{re.escape(alias)}\b", t):
            return code
    # Repli sur codes courts ("fr", "en", "ff", "ha") hors préposition "passer/parler/mettre en ..."
    cleaned = re.sub(r"\b(passer|parler|mettre|traduire|changer|ecrire)\s+en\b", " ", t)
    for alias in ("fr", "en", "ff", "ha"):
        if re.search(rf"\b{alias}\b", cleaned):
            return LANGUAGE_ALIASES[alias]
    return None


def _parse_rules(
    raw: str,
    channel: str = "ussd",
    input_type: str = "text",
    ussd_text: str | None = None,
    has_pending_tx: bool = False,
    awaiting_field: str | None = None,
    draft_op_type: str | None = None,
) -> NLUResult:
    t = raw.lower()

    # 0. Réinitialisation explicite du menu USSD (*123# ou chaine vide)
    if t in {"", "*123#", "00", "menu"}:
        return NLUResult(Intent.UNKNOWN, {"menu": True, "reset_draft": True})

    # 0b. Choix de langue par numéro ou code après avoir tapé "0" (awaiting_field == "language_choice")
    if awaiting_field == "language_choice":
        lang_order = ["dua", "ewo", "bas", "bbj", "byv", "fub", "hau", "bum", "wes", "fr", "en"]
        if t.isdigit():
            idx = int(t) - 1
            if 0 <= idx < len(lang_order):
                return NLUResult(Intent.LANGUAGE_SWITCH, {"target_language": lang_order[idx]})
        target = extract_target_language(raw)
        if target:
            return NLUResult(Intent.LANGUAGE_SWITCH, {"target_language": target})

    # 0c. Choix d'un bénéficiaire parmi des homonymes (awaiting_field == "candidate_choice")
    if awaiting_field == "candidate_choice":
        if t.isdigit() and 1 <= int(t) <= 9:
            return NLUResult(Intent.TRANSFER, {"candidate_index": int(t) - 1})
        ph = extract_phone(raw)
        if ph:
            return NLUResult(Intent.TRANSFER, {"to_phone": ph})
        ben = extract_beneficiary_name(raw, allow_bare=True)
        if ben:
            return NLUResult(Intent.TRANSFER, {"beneficiary": ben})

    # 1. Cas USSD menu numérique ou raccourci *
    if channel.lower() == "ussd" or input_type == "menu":
        if has_pending_tx:
            if t in {"1", "oui", "yes", "ok", "confirm", "confirmer", "yebe", "tabbitin", "tabbatar", "kanese", "kañese", "eme", "neebe", "hee", "timbisɛ", "timbise", "hémle", "hemle", "yôô", "yoo", "ŋ̀ŋ̂", "nng", "ŋ̂"}:
                return NLUResult(Intent.CONFIRM)
            if t in {"2", "non", "no", "cancel", "annuler", "tebe", "habbit", "soke", "joe", "jô'é", "bwa", "tehe", "kem", "timba", "shimbɛ", "bôg", "bog", "tɔ̀", "to", "ka'", "bili", "ben", "ŋŋ̀"}:
                return NLUResult(Intent.CANCEL)

        if "*" in t and not t.startswith("*"):
            parts = [p.strip() for p in t.split("*") if p.strip()]
            if parts and parts[0] == "2":
                amt = extract_amount(" ".join(parts[1:]))
                ph = extract_phone(" ".join(parts[1:]))
                return NLUResult(Intent.TRANSFER, {k: v for k, v in [("amount", amt), ("to_phone", ph)] if v})
            if parts and parts[0] == "5":
                amt = extract_amount(" ".join(parts[1:]))
                ph = extract_phone(" ".join(parts[1:]))
                return NLUResult(Intent.AIRTIME_PURCHASE, {k: v for k, v in [("amount", amt), ("to_phone", ph)] if v})

        if not awaiting_field:
            if t == "1":
                return NLUResult(Intent.BALANCE_INQUIRY)
            if t == "2":
                return NLUResult(Intent.TRANSFER)
            if t == "3":
                return NLUResult(Intent.FEE_INQUIRY)
            if t == "4":
                return NLUResult(Intent.TRANSACTION_HISTORY)
            if t == "5":
                return NLUResult(Intent.AIRTIME_PURCHASE)
            if t == "6":
                return NLUResult(Intent.BILL_PAYMENT)
            if t == "0":
                return NLUResult(Intent.LANGUAGE_SWITCH, {"show_options": True})

    # 2. Confirmation / Annulation / Correction (explicite cross-canal ou en attente)
    if re.search(r"\b(modifier|corriger|corrige|edit|gyara|canza|tyende|tyendé)\b", t) or (
        has_pending_tx and re.search(r"\b(changer|change|plutot|plutôt|instead|en fait|finalement|waylu|tukwa|henha|sûli|suli|shang|gyara|canza|tyende|tyendé)\b", t)
    ):
        params: dict[str, Any] = {}
        amt = extract_amount(raw)
        ph = extract_phone(raw)
        ben = extract_beneficiary_name(raw)
        if amt:
            params["amount"] = amt
        if ph:
            params["to_phone"] = ph
        if ben:
            params["beneficiary"] = ben
        return NLUResult(Intent.CORRECTION, params)

    if re.search(r"\b(annuler|cancel|habbit|timba|tebe|soke|jô'ôé|jô'é|jo'oe)\b", t) or (
        has_pending_tx and re.search(r"\b(non|no|stop|bwa|tehe|kem|bôg|bog|bili|ben|ka'|a'a|momo|2)\b", t)
    ):
        return NLUResult(Intent.CANCEL)

    if re.search(r"\b(confirmer|confirm|valider|validate|tabbitin|tabbatar|kañese|kanese|timbisɛ|timbise|hémle|hemle)\b", t) or (
        has_pending_tx and re.search(r"\b(oui|yes|yebe|eme|neebe|hee|yôô|yoo|eh|ôwé|owe|ok|1)\b", t)
    ):
        return NLUResult(Intent.CONFIRM)

    # 3. Changement de langue
    if re.search(r"\b(langue|language|parler|speak|switch|demgal|harshe|harshen|nkobo|nkobô|bwea|hop|ghom|passer en|change language)\b", t):
        target = extract_target_language(raw)
        if target:
            return NLUResult(Intent.LANGUAGE_SWITCH, {"target_language": target})
        return NLUResult(Intent.LANGUAGE_SWITCH, {"show_options": True})

    # 4. Explication de terminologie financière
    if re.search(r"\b(c'est quoi|qu'est-ce que|explique|signifie|veut dire|definition|définition|what is|meaning|explain|wetin be|ko woni|menene|me nene|nje e ne|dze a ne|jé a ne|je a ne|kii ye|ka ba|kə ne)\b", t):
        for term_key, kws in TERM_KEYWORDS.items():
            if any(k in t for k in kws):
                return NLUResult(Intent.TERM_EXPLANATION, {"term": term_key})
        return NLUResult(Intent.TERM_EXPLANATION, {"term": "frais"})

    # 5. Consultation de solde (avec et sans le mot "solde")
    if re.search(
        r"\b(solde|balance|combien j'ai|combien il me reste|mon argent|voir mon compte|mon compte|moni weh remain|ceede keddiide|ceede maa|ragowar kudi|kudina|nawa ne|moné wom|mone wom|moné a li'i|mone a li'i|mòni wom|moni wom|mòni a lig|moni a lig|a lig ma|a ne va a ne tan|mone ma tabe|mone woe|moni ma dia|moni mongo|moni u nkon|moni won|nkap ya tse|nkap po|nkap bu)\b",
        t,
    ):
        return NLUResult(Intent.BALANCE_INQUIRY)

    # 6. Historique des transactions
    if re.search(r"\b(historique|history|dernieres operations|dernières opérations|transactions|releve|relevé|golle ceede|tarihi|tarihina|mam me lôteya|mam me loteya|alom ya nde|bola|bilon|bivul)\b", t):
        return NLUResult(Intent.TRANSACTION_HISTORY, {"limit": 5})

    # 7. Demande de frais (ne jamais inventer un montant si l'utilisateur ne l'a pas fourni)
    if re.search(r"\b(frais|fee|fees|charges|tarif|commission|njobdi|njoɓdi|kudin aiki|kuɗin aiki|fre|njoa|nsas|combien coute|combien coûte|cout|coût)\b", t):
        amt = extract_amount(raw)
        op_type = "transfer"
        if re.search(r"\b(facture|bill|eneo|camwater|canal)\b", t):
            op_type = "bill"
        elif re.search(r"\b(credit|crédit|airtime|mtn|orange)\b", t):
            op_type = "airtime"
        elif re.search(r"\b(retrait|withdrawal)\b", t):
            op_type = "withdrawal"
        params_fee: dict[str, Any] = {"type": op_type}
        if amt is not None:
            params_fee["amount"] = amt
        return NLUResult(Intent.FEE_INQUIRY, params_fee)

    # 8. Suite multi-tour frais / crédit / facture en attente de montant
    if awaiting_field and draft_op_type == "fee":
        amt = extract_amount(raw)
        return NLUResult(Intent.FEE_INQUIRY, {"amount": amt, "type": "transfer"} if amt else {})

    if awaiting_field and draft_op_type == "airtime":
        amt = extract_amount(raw)
        ph = extract_phone(raw)
        _, op = extract_biller_or_operator(raw)
        return NLUResult(Intent.AIRTIME_PURCHASE, {k: v for k, v in [("operator", op), ("amount", amt), ("to_phone", ph)] if v})

    if awaiting_field and draft_op_type == "bill":
        amt = extract_amount(raw)
        biller, _ = extract_biller_or_operator(raw)
        return NLUResult(Intent.BILL_PAYMENT, {k: v for k, v in [("biller", biller), ("amount", amt)] if v})

    # 9. Paiement de facture
    biller, operator = extract_biller_or_operator(raw)
    if biller or re.search(r"\b(facture|bill|lissafi|electricite|électricité|wutar lantarki|eau|abonnement)\b", t):
        amt = extract_amount(raw)
        return NLUResult(Intent.BILL_PAYMENT, {"biller": biller or "ENEO", "amount": amt})

    # 10. Achat de crédit téléphonique
    if operator or re.search(r"\b(credit|crédit|airtime|katin waya|sayen kati|recharge|unites|unités)\b", t):
        amt = extract_amount(raw)
        ph = extract_phone(raw)
        return NLUResult(Intent.AIRTIME_PURCHASE, {"operator": operator, "amount": amt, "to_phone": ph})

    # 10b. Retrait d'argent (USSD / GAB ATM — multiples de 5 000 FCFA sur ATM)
    if (
        re.search(r"\b(retrait|retirer|withdraw|withdrawal|comot moni|cire kudi|ittude|busa moni|pémés|pemes)\b", t)
        or (awaiting_field and draft_op_type == "withdrawal")
    ):
        amt = extract_amount(raw)
        return NLUResult(Intent.TRANSFER, {"op_subtype": "withdrawal", **({"amount": amt} if amt else {})})

    # 11. Transfert d'argent (ou suite multi-tour transfert)
    if (
        re.search(r"\b(envoyer|envoie|envoies|transferer|transférer|transfere|transfère|transfert|transfer|send|virement|aika|nel|neldude|lom|lôm|loma|lóma|lémèl|lemel|ntúm|ntum|tom)\b", t)
        or awaiting_field in ("amount", "beneficiary")
    ):
        amt = extract_amount(raw)
        ph = extract_phone(raw)
        ben = extract_beneficiary_name(raw, allow_bare=(awaiting_field == "beneficiary"))
        params = {}
        if amt:
            params["amount"] = amt
        if ph:
            params["to_phone"] = ph
        if ben:
            params["beneficiary"] = ben
        return NLUResult(Intent.TRANSFER, params)

    # 12. Montant ou numéro seul
    amt_only = extract_amount(raw)
    ph_only = extract_phone(raw)
    if amt_only or ph_only:
        params = {}
        if amt_only:
            params["amount"] = amt_only
        if ph_only:
            params["to_phone"] = ph_only
        return NLUResult(Intent.TRANSFER, params)

    return NLUResult(Intent.UNKNOWN)


def parse_intent(
    text: str,
    channel: str = "ussd",
    input_type: str = "text",
    ussd_text: str | None = None,
    has_pending_tx: bool = False,
    awaiting_field: str | None = None,
    draft_op_type: str | None = None,
    language: str | None = None,
) -> NLUResult:
    """Analyse l'entrée utilisateur avec repli NMT local si phrase inconnue en langue nationale."""
    raw = (text or "").strip()
    res = _parse_rules(
        raw=raw,
        channel=channel,
        input_type=input_type,
        ussd_text=ussd_text,
        has_pending_tx=has_pending_tx,
        awaiting_field=awaiting_field,
        draft_op_type=draft_op_type,
    )
    if res.intent == Intent.UNKNOWN and not res.parameters.get("menu") and len(raw.split()) >= 2:
        pivoted = _pivot_to_french(raw, language)
        if pivoted:
            res2 = _parse_rules(
                raw=pivoted,
                channel=channel,
                input_type="text",
                ussd_text=ussd_text,
                has_pending_tx=has_pending_tx,
                awaiting_field=awaiting_field,
                draft_op_type=draft_op_type,
            )
            if res2.intent != Intent.UNKNOWN:
                # Conserver les chiffres/téléphones extraits de l'entrée brute originale
                amt = extract_amount(raw)
                ph = extract_phone(raw)
                if amt and "amount" not in res2.parameters:
                    res2.parameters["amount"] = amt
                if ph and "to_phone" not in res2.parameters:
                    res2.parameters["to_phone"] = ph
                return res2
    return res
