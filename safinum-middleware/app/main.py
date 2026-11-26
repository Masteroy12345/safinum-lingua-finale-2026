"""Point d'entrée FastAPI de Safinum Lingua — Infrastructure Linguistique Universelle.

Gère les DEUX contrats officiels de la passerelle Safinum :
1. Canal USSD conversationnel (`input` -> réponse conversationnelle GSM-7 <= 182 septets + banque).
2. Canaux Mobile et Web (`type == "ui_translation"` -> traduction d'écrans JSON avec placeholders intacts & max_chars).
"""
from __future__ import annotations

import csv
import re
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from .bank_client import BankApiError, BankClient
from .config import settings
from .gsm7 import fit_channel_constraints
from .languages import (
    CAMEROON_NATIONAL_LANGUAGES,
    SUPPORTED_LANGUAGES,
    detect_language,
    fmt_amount,
    get_error_text,
    get_term_explanation,
    get_text,
    normalize_language,
    translate_phrase,
)
from .models import (
    GatewayRequest,
    GatewayResponse,
    Intent,
    InterpretationBody,
    MiddlewareResponseBody,
    TransactionBody,
    TransactionStatus,
)
from .nlu import parse_intent
from .phonetics import GRAMMAR_RULES, build_audio_payload, synthesize_wav_bytes
from .session_store import normalize_phone, store
from .ui_translator import UI_TRANSLATIONS, handle_ui_translation

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NATIVE_AUDIO_DIR = (
    _REPO_ROOT / "extantion-safinum-main" / "enregistrements_a_verifier"
    if (_REPO_ROOT / "extantion-safinum-main" / "enregistrements_a_verifier").is_dir()
    else _REPO_ROOT / "extantion-safinum-main" / "extantion-safinum-main" / "enregistrements_a_verifier"
)

app = FastAPI(
    title="Safinum Lingua — Universal Linguistic Middleware",
    version="2.0.0",
    description="Infrastructure linguistique multicanale (USSD conversationnel + Mobile/Web ui_translation + SMS/ATM/IVR v2) pour le SAFINUM Innovate Challenge 2026.",
)

bank_client = BankClient()


async def _recover_pending_tx(session, phone: str, trace_id: str, base_url: str) -> str | None:
    """Récupère une transaction `pending` côté API bancaire si la session locale n'en a pas (cross-canal / redémarrage)."""
    if session.pending_tx_id:
        return session.pending_tx_id
    hist = await bank_client.get_transactions(phone, 5, trace_id, base_url)
    txs = hist.get("transactions") or hist.get("data") or []
    pending_tx = next((x for x in txs if str(x.get("status", "")).lower() == "pending"), None)
    if pending_tx:
        session.pending_tx_id = pending_tx.get("id") or pending_tx.get("transaction_id")
        session.pending_op = {
            "type": pending_tx.get("type", "transfer"),
            "amount": pending_tx.get("amount", 0),
            "to": pending_tx.get("to") or pending_tx.get("beneficiary", ""),
            "beneficiary": pending_tx.get("beneficiary") or pending_tx.get("to", ""),
        }
    return session.pending_tx_id


def _build_response(
    req: GatewayRequest,
    lang: str,
    raw_text: str,
    intent: Intent,
    params: dict[str, Any] | None = None,
    end_session: bool = False,
    options: list[str] | None = None,
    tx_id: str | None = None,
    tx_status: TransactionStatus = TransactionStatus.NONE,
    started_at: float | None = None,
) -> GatewayResponse:
    fitted_text, gsm_meta = fit_channel_constraints(
        raw_text,
        channel=req.channel,
        max_chars=req.constraints.max_chars,
        charset=req.constraints.charset,
    )
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 1) if started_at else 0.0
    store.log_diagnostic({
        "trace_id": req.trace_id,
        "channel": req.channel,
        "mode": "ussd",
        "phone": normalize_phone(req.phone),
        "language": lang,
        "intent": intent.value,
        "parameters": params or {},
        "tx_id": tx_id,
        "tx_status": tx_status.value,
        "latency_ms": elapsed_ms,
        "gsm_meta": gsm_meta,
        "response_preview": fitted_text,
    })
    return GatewayResponse(
        response=MiddlewareResponseBody(
            text=fitted_text,
            end_session=end_session,
            options=options or [],
        ),
        interpretation=InterpretationBody(
            intent=intent,
            parameters=params or {},
            language=lang,
        ),
        transaction=TransactionBody(id=tx_id, status=tx_status),
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "ok": True,
        "service": "safinum-lingua-middleware",
        "team_id": settings.team_id,
        "languages": list(SUPPORTED_LANGUAGES.keys()),
        "channels": ["ussd", "mobile", "web", "sms", "atm", "ivr"],
        "contracts": ["ussd_conversational", "ui_translation"],
    }


@app.get("/api/diagnostics")
async def get_diagnostics() -> dict[str, Any]:
    return {"items": store.get_diagnostics()}


@app.get("/api/grammar")
async def get_grammar() -> dict[str, Any]:
    """Expose les règles de conjugaison, pronoms et phonologie des langues camerounaises."""
    return {"languages": GRAMMAR_RULES}


@app.post("/api/phonetics")
async def convert_phonetics(payload: dict[str, str]) -> dict[str, Any]:
    """Convertit un texte financier en transcription IPA et script audio prêt pour TTS."""
    text = payload.get("text", "")
    lang = normalize_language(payload.get("language")) or "fr"
    return build_audio_payload(text, lang)


@app.post("/api/audio/tts")
@app.get("/api/audio/tts")
async def tts_audio(text: str = "", language: str = "fr", payload: dict[str, str] | None = None):
    """Synthèse audio WAV locale (Meta MMS-TTS) avec repli phonétique structuré."""
    if payload:
        text = payload.get("text", text)
        language = payload.get("language", language)
    lang = normalize_language(language) or "fr"
    wav, info = synthesize_wav_bytes(text, lang)
    if wav:
        return Response(content=wav, media_type="audio/wav", headers={"X-TTS-Engine": info})
    audio_meta = build_audio_payload(text, lang)
    return JSONResponse({"fallback": "browser_tts", "reason": info, **audio_meta})


@app.post("/api/translate")
async def translate_endpoint(payload: dict[str, str]) -> dict[str, Any]:
    """Traduit un mot ou une phrase complète en protégeant montants/numéros/noms/références, avec sortie IPA, GSM-7 et audio."""
    text = payload.get("text", "")
    src = normalize_language(payload.get("source_language")) or detect_language(text, fallback="fr")
    lang = normalize_language(payload.get("language")) or "fr"
    res = translate_phrase(text, lang)
    audio = build_audio_payload(res["translated"], lang)
    fitted_ussd, gsm_meta = fit_channel_constraints(res["translated"], channel="ussd", max_chars=182, charset="gsm7")
    # Extraire les entités bancaires protégées visibles
    import re as _re
    protected_found = _re.findall(
        r"\{[a-z_]+\}|(?:TRX|SAF)-[A-Za-z0-9\-]+|(?:\+?237[\s\-\.]?)?6[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}|\b\d[\d\s\.,]*\s*(?:FCFA|XAF|CFA)\b|\b\d+(?:[\s\.,]\d+)*\b|\b(?:ENEO|CAMWATER|CANAL\+?|CAMTEL|MTN|ORANGE|Safinum(?:\s+Pay)?)\b",
        text,
        flags=_re.IGNORECASE,
    )
    client_names = [
        m.group(2)
        for m in _re.finditer(
            r"(\b(?:[àa]|pour|de|vers|chez|give|to|from|[Bb]onjour|[Hh]ello|[Mm]bolo|[Ss]annu)\s+)([A-ZÀ-Ÿ][a-zà-ÿ'\-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ'\-]+)*)",
            text,
        )
    ]
    for cn in client_names:
        if cn not in protected_found:
            protected_found.append(cn)
    return {
        "source_language": src,
        "target_language": lang,
        "protected_entities": protected_found,
        "gsm7_preview": fitted_ussd,
        "gsm_meta": gsm_meta,
        **res,
        **audio,
    }


@app.post("/api/translate-all")
async def translate_all_endpoint(payload: dict[str, str]) -> dict[str, Any]:
    """Traduit une phrase dans toutes les 7 langues camerounaises (dont le Pidgin Camerounais) simultanément."""
    text = payload.get("text", "")
    src = normalize_language(payload.get("source_language")) or detect_language(text, fallback="fr")
    results: dict[str, Any] = {}
    for code, label in CAMEROON_NATIONAL_LANGUAGES.items():
        res = translate_phrase(text, code)
        audio = build_audio_payload(res["translated"], code)
        fitted_ussd, gsm_meta = fit_channel_constraints(res["translated"], channel="ussd", max_chars=182, charset="gsm7")
        results[code] = {
            "label": label,
            "translated": res["translated"],
            "mode": res["mode"],
            "ipa": audio["ipa"],
            "web_phonetic": audio["web_phonetic"],
            "tts_script": audio["tts_script"],
            "tts_voice_lang": audio["tts_voice_lang"],
            "neural_tts_available": audio["neural_tts_available"],
            "gsm7_preview": fitted_ussd,
            "gsm7_septets": gsm_meta["septets"],
        }
    return {"source_language": src, "text": text, "translations": results}


@app.get("/api/ui-keys")
async def get_ui_keys(language: str = "dua") -> dict[str, Any]:
    """Retourne les 89 clés officielles de l'application Mobile/Web traduites dans la langue demandée."""
    lang = normalize_language(language) or "dua"
    fr_src = UI_TRANSLATIONS["fr"]
    payload = {
        "language": lang,
        "strings": {k: {"text": v, "context": "ui"} for k, v in fr_src.items()},
    }
    tr = handle_ui_translation(payload, fallback_lang=lang)
    items = []
    for k, fr_val in fr_src.items():
        tr_val = tr["strings"].get(k, "")
        audio = build_audio_payload(tr_val, lang)
        items.append({
            "key": k,
            "source_fr": fr_val,
            "translated": tr_val,
            "ipa": audio["ipa"],
            "tts_script": audio["tts_script"],
            "tts_voice_lang": audio["tts_voice_lang"],
            "neural_tts_available": audio["neural_tts_available"],
        })
    return {"language": lang, "count": len(items), "items": items}


@app.get("/api/jury-scenarios")
async def get_jury_scenarios() -> dict[str, Any]:
    """Retourne les 10 scénarios officiels du Jury prêts à être exécutés en 1 clic avec génération vocale automatique."""
    scenarios = [
        {
            "id": 1,
            "code": "balance",
            "title": "1. Consultation de solde (sans prononcer « solde »)",
            "channel": "ussd",
            "language": "ewo",
            "description": "L'utilisateur demande combien d'argent il lui reste en Ewondo sans utiliser le mot français « solde ».",
            "steps": [
                {"channel": "ussd", "language": "ewo", "text": "Mbolo, mòni wom a lig ma a ne tan ya ?", "label": "Demande en Ewondo"}
            ],
        },
        {
            "id": 2,
            "code": "transfer",
            "title": "2. Transfert d'argent avec confirmation en 2 tours",
            "channel": "ussd",
            "language": "dua",
            "description": "Tour 1 : Initiation du transfert en Duálá (statut pending + relecture). Tour 2 (nouveau X-Trace-Id) : Confirmation explicite.",
            "steps": [
                {"channel": "ussd", "language": "dua", "text": "loma 5000 FCFA na 677000002", "label": "Tour 1 : Initier 5 000 FCFA (pending)"},
                {"channel": "ussd", "language": "dua", "text": "1", "label": "Tour 2 : Confirmer (Hee / Timbisɛ)"},
            ],
        },
        {
            "id": 3,
            "code": "fees",
            "title": "3. Demande de frais (borne de palier 5 000 / 25 000 FCFA)",
            "channel": "ussd",
            "language": "bas",
            "description": "L'utilisateur demande les frais d'envoi pour 25 000 FCFA en Ɓasaá -> appel GET /fees.",
            "steps": [
                {"channel": "ussd", "language": "bas", "text": "nsas inyu 25000 FCFA", "label": "Demande frais 25 000 FCFA en Ɓasaá"}
            ],
        },
        {
            "id": 4,
            "code": "history",
            "title": "4. Historique des opérations",
            "channel": "ussd",
            "language": "bbj",
            "description": "Consultation des dernières transactions en Ghɔmálá' formatée <= 182 septets GSM-7.",
            "steps": [
                {"channel": "ussd", "language": "bbj", "text": "bivul bi nkap", "label": "Demande historique en Ghɔmálá'"}
            ],
        },
        {
            "id": 5,
            "code": "correction",
            "title": "5. Correction avant confirmation (recalcul des frais)",
            "channel": "ussd",
            "language": "fub",
            "description": "L'utilisateur lance un envoi de 5 000 FCFA (frais 50), corrige le montant à 10 000 FCFA avant de confirmer (frais recalculés à 150), puis valide.",
            "steps": [
                {"channel": "ussd", "language": "fub", "text": "nel 5000 FCFA e 677000002", "label": "Tour 1 : Envoi 5 000 FCFA"},
                {"channel": "ussd", "language": "fub", "text": "waylu 10000 FCFA", "label": "Tour 2 : Corriger à 10 000 FCFA (POST /update)"},
                {"channel": "ussd", "language": "fub", "text": "tabbitin", "label": "Tour 3 : Confirmer 10 000 FCFA"},
            ],
        },
        {
            "id": 6,
            "code": "ambiguous",
            "title": "6. Demande ambiguë (CLARIFICATION_NEEDED sans deviner)",
            "channel": "ussd",
            "language": "byv",
            "description": "Envoi sans préciser le destinataire en Mə̀dûmbà : le middleware retourne CLARIFICATION_NEEDED sans jamais deviner.",
            "steps": [
                {"channel": "ussd", "language": "byv", "text": "ntum 5000 FCFA", "label": "Tour 1 : Montant sans destinataire -> CLARIFICATION_NEEDED"},
                {"channel": "ussd", "language": "byv", "text": "677000002", "label": "Tour 2 : Préciser le destinataire"},
            ],
        },
        {
            "id": 7,
            "code": "insufficient_funds",
            "title": "7. Solde insuffisant (traduit sans code brut INSUFFICIENT_FUNDS)",
            "channel": "ussd",
            "language": "wes",
            "description": "Tentative d'envoi supérieur au solde en Pidgin Camerounais : explication claire dans la langue, jamais le code brut.",
            "steps": [
                {"channel": "ussd", "language": "wes", "text": "send 450000 FCFA give 677000002", "label": "Envoi > Solde en Pidgin Camerounais"}
            ],
        },
        {
            "id": 8,
            "code": "language_switch",
            "title": "8. Changement de langue en cours de conversation",
            "channel": "ussd",
            "language": "ewo",
            "description": "Commencer un transfert en Ewondo, basculer en Duálá au milieu du parcours sans perdre l'opération.",
            "steps": [
                {"channel": "ussd", "language": "ewo", "text": "lom 5000 FCFA a 677000002", "label": "Tour 1 : Initier en Ewondo"},
                {"channel": "ussd", "language": None, "text": "bwea duala", "label": "Tour 2 : Basculer en Duálá (session préservée)"},
                {"channel": "ussd", "language": "dua", "text": "timbise", "label": "Tour 3 : Confirmer en Duálá"},
            ],
        },
        {
            "id": 9,
            "code": "multichannel",
            "title": "9. Parcours multicanal (USSD -> Mobile/Web sans double exécution)",
            "channel": "ussd",
            "language": "fub",
            "description": "Initier en USSD avec le numéro 237677000001, puis reprendre et confirmer sur Mobile avec le même numéro.",
            "steps": [
                {"channel": "ussd", "language": "fub", "text": "nel 5000 FCFA e 677000002", "label": "Tour 1 (Canal USSD) : Créer transaction pending"},
                {"channel": "mobile", "language": "fub", "text": "tabbitin", "label": "Tour 2 (Canal Mobile) : Retrouver & Confirmer sans doublon"},
            ],
        },
        {
            "id": 10,
            "code": "terminology",
            "title": "10. Explication de la terminologie financière (frais, plafond, bénéficiaire)",
            "channel": "ussd",
            "language": "dua",
            "description": "Explication pédagogique accessible à une personne non bancarisée en langue nationale.",
            "steps": [
                {"channel": "ussd", "language": "dua", "text": "nje e ne njoa ?", "label": "Expliquer « frais (njoa) » en Duálá"},
                {"channel": "ussd", "language": "ewo", "text": "dze a ne plafon ?", "label": "Expliquer « plafond » en Ewondo"},
                {"channel": "ussd", "language": "wes", "text": "wetin be beneficiary ?", "label": "Expliquer « bénéficiaire » en Pidgin Camerounais"},
            ],
        },
    ]
    return {"count": len(scenarios), "items": scenarios}


@app.get("/api/native-recordings")
async def list_native_recordings() -> dict[str, Any]:
    """Liste les 18 enregistrements audio de locuteurs natifs (Ewondo, Fulfulde, Pidgin) présents dans le projet."""
    idx_file = _NATIVE_AUDIO_DIR / "index.csv"
    if not idx_file.is_file():
        return {"items": []}
    items: list[dict[str, Any]] = []
    with idx_file.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            lang_folder = (row.get("langue") or "").strip()
            filename = (row.get("fichier") or "").strip()
            file_path = _NATIVE_AUDIO_DIR / lang_folder / filename
            if file_path.is_file():
                items.append({
                    "language": lang_folder,
                    "filename": filename,
                    "meaning_fr": row.get("sens en français", ""),
                    "speaker": row.get("locuteur / auteur", ""),
                    "license": row.get("licence", ""),
                    "notes": row.get("à vérifier", ""),
                    "audio_url": f"/api/native-audio/{lang_folder}/{filename}",
                })
    return {"count": len(items), "items": items}


@app.get("/api/native-audio/{lang_folder}/{filename}")
async def serve_native_audio(lang_folder: str, filename: str):
    """Sert un fichier audio natif (.wav / .mp3) vérifié."""
    if ".." in lang_folder or ".." in filename or "/" in lang_folder or "/" in filename:
        raise HTTPException(status_code=400, detail="Chemin invalide")
    target = (_NATIVE_AUDIO_DIR / lang_folder / filename).resolve()
    if not target.is_file() or not str(target).startswith(str(_NATIVE_AUDIO_DIR.resolve())):
        raise HTTPException(status_code=404, detail="Fichier audio introuvable")
    media_type = "audio/mpeg" if filename.lower().endswith(".mp3") else "audio/wav"
    return FileResponse(str(target), media_type=media_type)


@app.get("/api/native-bank")
async def native_bank_index(language: str = "ewo") -> dict[str, Any]:
    """Référentiel tonal et prosodique SOREVA (CC-BY-4.0) : 150 phrases par langue, tonalité copiée dans la voix unique ElevenLabs."""
    from . import native_voice_bank as nvb

    lang = normalize_language(language) or "ewo"
    phrases = nvb.list_phrases(lang)
    return {
        "source": "SOREVA (OlameMend/soreva, Goethe-Institut) - CC-BY-4.0",
        "voice": "Brian (Voix d'homme unique ElevenLabs avec transfert de tonalité & prosodie SOREVA)",
        "prosody_profile": nvb.get_language_voice_settings(lang),
        "stats": nvb.bank_stats(),
        "language": lang,
        "count": len(phrases),
        "items": [
            {**p, "audio_url": f"/api/native-bank/audio?language={lang}&clip={p['clip']}"}
            for p in phrases
        ],
    }


@app.get("/api/native-bank/audio")
async def native_bank_audio(language: str, clip: str):
    """Lit la phrase tonale SOREVA via l'unique voix masculine ElevenLabs (sans jouer le fichier audio brut du dataset)."""
    from . import native_voice_bank as nvb

    lang = normalize_language(language) or "ewo"
    if not re.fullmatch(r"[A-Za-z0-9_\-]+\.wav", clip or ""):
        raise HTTPException(status_code=400, detail="Clip invalide")
    entry = nvb.load_bank().get(lang, {}).get(f"__clip__:{clip}")
    if not entry:
        raise HTTPException(status_code=404, detail="Clip introuvable")
    wav, eng = synthesize_wav_bytes(entry["aglc"], lang)
    if not wav:
        raise HTTPException(status_code=503, detail=eng)
    return Response(content=wav, media_type="audio/wav", headers={"X-TTS-Engine": eng})


@app.post("/middleware")
async def handle_gateway(request: Request):
    t0 = time.perf_counter()
    payload = await request.json()
    header_trace = request.headers.get("X-Trace-Id") or payload.get("trace_id") or "trace-missing"

    # --- CONTRAT MOBILE & WEB : TRADUCTION D'ÉCRANS (`type == "ui_translation"`) ---
    if payload.get("type") == "ui_translation":
        phone = normalize_phone(payload.get("phone") or "")
        session = store.get_or_create(phone) if phone else None
        fallback_lang = session.language if session else "fr"
        ui_resp = handle_ui_translation(payload, fallback_lang=fallback_lang)
        if session:
            session.language = ui_resp["language"]
            session.last_channel = str(payload.get("channel") or "web").lower()
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        keys_count = len(ui_resp.get("strings") or {})
        store.log_diagnostic({
            "trace_id": header_trace,
            "channel": payload.get("channel", "web"),
            "mode": "ui_translation",
            "phone": phone or "-",
            "language": ui_resp["language"],
            "intent": f"UI:{payload.get('screen', 'screen')}",
            "parameters": {"keys": keys_count, "screen": payload.get("screen")},
            "tx_id": None,
            "tx_status": "none",
            "latency_ms": elapsed_ms,
            "gsm_meta": {"septets": keys_count, "limit": keys_count, "charset": "utf8"},
            "response_preview": f"{keys_count} cles UI ({payload.get('screen', '-')}) -> {ui_resp['language']}",
        })
        return JSONResponse(ui_resp)

    # --- CONTRAT USSD / CONVERSATIONNEL ---
    if "trace_id" not in payload or not payload.get("trace_id"):
        payload["trace_id"] = header_trace
    req = GatewayRequest.model_validate(payload)
    trace_id = request.headers.get("X-Trace-Id") or req.trace_id
    phone = normalize_phone(req.phone)
    session = store.get_or_create(phone)
    session.last_channel = req.channel.lower()
    base_url = req.bank_api.base_url or settings.bank_api_url
    user_text = (req.input.text or "").strip()

    # 1. Résolution ou détection automatique de la langue (si language=null)
    req_lang = normalize_language(req.language)
    if req_lang:
        lang = req_lang
        session.language = lang
    else:
        lang = detect_language(user_text, fallback=session.language or "fr")
        session.language = lang

    # 2. Analyse NLU (déterministe + repli neuronal CTranslate2 si nécessaire)
    nlu = parse_intent(
        text=user_text,
        channel=req.channel,
        input_type=req.input.type,
        ussd_text=req.input.ussd_text,
        has_pending_tx=bool(session.pending_tx_id),
        awaiting_field=session.awaiting_field,
        draft_op_type=session.draft_op_type,
        language=lang,
    )

    if nlu.parameters.get("reset_draft"):
        session.awaiting_field = None
        session.draft_op_type = None
        session.draft_transfer = {}
        session.candidate_choices = []

    try:
        # --- CHANGEMENT DE LANGUE ---
        if nlu.intent == Intent.LANGUAGE_SWITCH:
            target = nlu.parameters.get("target_language")
            if target and target in SUPPORTED_LANGUAGES:
                session.language = target
                if session.awaiting_field == "language_choice":
                    session.awaiting_field = None
                msg = get_text(target, "lang_switched", req.channel)
                return _build_response(req, target, msg, Intent.LANGUAGE_SWITCH, {"language": target}, started_at=t0)
            session.awaiting_field = "language_choice"
            opts = [f"{k}:{v}" for k, v in CAMEROON_NATIONAL_LANGUAGES.items()]
            msg = "Langues camerounaises: " + ", ".join(f"{i+1}.{k}" for i, k in enumerate(CAMEROON_NATIONAL_LANGUAGES.keys()))
            return _build_response(req, lang, msg, Intent.LANGUAGE_SWITCH, {"available": list(CAMEROON_NATIONAL_LANGUAGES.keys())}, options=opts, started_at=t0)

        # --- EXPLICATION TERMINOLOGIE FINANCIÈRE ---
        if nlu.intent == Intent.TERM_EXPLANATION:
            term = nlu.parameters.get("term", "frais")
            msg = get_term_explanation(lang, term)
            return _build_response(req, lang, msg, Intent.TERM_EXPLANATION, {"term": term}, started_at=t0)

        # --- CONSULTATION DE SOLDE ---
        if nlu.intent == Intent.BALANCE_INQUIRY:
            acct = await bank_client.get_account(phone, trace_id, base_url)
            name = acct.get("holder_name") or acct.get("name") or phone
            bal = acct.get("balance", 0)
            msg = get_text(lang, "balance", req.channel, name=name, balance=fmt_amount(bal), phone=phone)
            return _build_response(
                req, lang, msg, Intent.BALANCE_INQUIRY,
                {"balance": bal, "currency": acct.get("currency", "XAF")},
                end_session=(req.channel.lower() == "ussd"),
                started_at=t0,
            )

        # --- HISTORIQUE DES TRANSACTIONS ---
        if nlu.intent == Intent.TRANSACTION_HISTORY:
            limit = int(nlu.parameters.get("limit", 5))
            res = await bank_client.get_transactions(phone, limit, trace_id, base_url)
            txs = res.get("transactions") or res.get("data") or []
            if not txs:
                msg = get_text(lang, "history_empty", req.channel)
            else:
                lines = [get_text(lang, "history_header", req.channel, count=len(txs))]
                for tx in txs[:3 if req.channel.lower() == "ussd" else 5]:
                    amt = fmt_amount(tx.get("amount", 0))
                    ttype = tx.get("type", "tx")
                    to_acc = tx.get("to") or tx.get("beneficiary") or ""
                    lines.append(f"- {ttype}: {amt} FCFA {to_acc}".strip())
                msg = "\n".join(lines)
            return _build_response(req, lang, msg, Intent.TRANSACTION_HISTORY, {"count": len(txs)}, started_at=t0)

        # --- DEMANDE DE FRAIS ---
        if nlu.intent == Intent.FEE_INQUIRY:
            amt = nlu.parameters.get("amount")
            op_type = nlu.parameters.get("type") or session.draft_transfer.get("type", "transfer")
            if not amt:
                session.awaiting_field = "amount"
                session.draft_op_type = "fee"
                session.draft_transfer = {"type": op_type}
                msg = get_text(lang, "ask_amount", req.channel)
                return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"type": op_type}, started_at=t0)
            session.awaiting_field = None
            session.draft_op_type = None
            session.draft_transfer = {}
            fee_res = await bank_client.get_fees(op_type, int(amt), trace_id, base_url)
            fee_val = fee_res.get("fee", 0)
            total_val = fee_res.get("total", int(amt) + fee_val)
            msg = get_text(
                lang, "fees", req.channel,
                amount=fmt_amount(amt), op_type=op_type, fee=fmt_amount(fee_val), total=fmt_amount(total_val),
            )
            return _build_response(
                req, lang, msg, Intent.FEE_INQUIRY,
                {"amount": int(amt), "type": op_type, "fee": fee_val, "total": total_val, "currency": "XAF"},
                started_at=t0,
            )

        # --- CONFIRMATION (TOUR 2 STRICT : JAMAIS LE MÊME X-Trace-Id) ---
        if nlu.intent == Intent.CONFIRM:
            await _recover_pending_tx(session, phone, trace_id, base_url)
            if not session.pending_tx_id:
                msg = get_text(lang, "no_pending", req.channel)
                return _build_response(req, lang, msg, Intent.CONFIRM, started_at=t0)
            if session.pending_tx_trace_id == trace_id:
                msg = get_text(lang, "no_pending", req.channel)
                return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, started_at=t0)

            tx_id = session.pending_tx_id
            conf = await bank_client.confirm_transaction(tx_id, trace_id, base_url)
            amt = conf.get("amount") if conf.get("amount") is not None else session.pending_op.get("amount", 0)
            confirmed_id = conf.get("id") or tx_id
            store.clear_pending(session)
            msg = get_text(lang, "confirmed", req.channel, tx_id=confirmed_id, amount=fmt_amount(amt))
            return _build_response(
                req, lang, msg, Intent.CONFIRM,
                {"transaction_id": confirmed_id, "amount": amt, "currency": conf.get("currency", "XAF")},
                end_session=(req.channel.lower() == "ussd"),
                tx_id=confirmed_id,
                tx_status=TransactionStatus.CONFIRMED,
                started_at=t0,
            )

        # --- ANNULATION ---
        if nlu.intent == Intent.CANCEL:
            await _recover_pending_tx(session, phone, trace_id, base_url)
            if session.pending_tx_id:
                tx_id = session.pending_tx_id
                await bank_client.cancel_transaction(tx_id, trace_id, base_url)
                store.clear_pending(session)
                msg = get_text(lang, "cancelled", req.channel)
                return _build_response(
                    req, lang, msg, Intent.CANCEL, {"transaction_id": tx_id},
                    end_session=(req.channel.lower() == "ussd"),
                    tx_id=tx_id, tx_status=TransactionStatus.CANCELLED, started_at=t0,
                )
            store.clear_pending(session)
            msg = get_text(lang, "cancelled", req.channel)
            return _build_response(req, lang, msg, Intent.CANCEL, end_session=(req.channel.lower() == "ussd"), started_at=t0)

        # --- CORRECTION AVANT CONFIRMATION ---
        if nlu.intent == Intent.CORRECTION:
            await _recover_pending_tx(session, phone, trace_id, base_url)
            if not session.pending_tx_id:
                msg = get_text(lang, "ask_correction", req.channel)
                return _build_response(req, lang, msg, Intent.CORRECTION, started_at=t0)
            update_payload: dict[str, Any] = {}
            if "amount" in nlu.parameters:
                update_payload["amount"] = nlu.parameters["amount"]
                session.pending_op["amount"] = nlu.parameters["amount"]
            if "to_phone" in nlu.parameters:
                update_payload["to"] = nlu.parameters["to_phone"]
                session.pending_op["to"] = nlu.parameters["to_phone"]
                session.pending_op["beneficiary"] = nlu.parameters["to_phone"]
            elif "beneficiary" in nlu.parameters:
                ben_res = await bank_client.search_beneficiaries(nlu.parameters["beneficiary"], None, trace_id, base_url)
                cands = ben_res.get("beneficiaries") or ben_res.get("candidates") or ben_res.get("data") or []
                if len(cands) == 1:
                    update_payload["to"] = cands[0].get("phone")
                    session.pending_op["to"] = cands[0].get("phone")
                    session.pending_op["beneficiary"] = cands[0].get("name") or cands[0].get("phone")
            if not update_payload:
                msg = get_text(lang, "ask_correction", req.channel)
                return _build_response(req, lang, msg, Intent.CORRECTION, started_at=t0)

            updated = await bank_client.update_transaction(session.pending_tx_id, update_payload, trace_id, base_url)
            amt = updated.get("amount", session.pending_op.get("amount", 0))
            fee_val = updated.get("fee", 0)
            total_val = updated.get("total", amt + fee_val)
            ben = session.pending_op.get("beneficiary") or session.pending_op.get("to", "")
            to_phone = session.pending_op.get("to", "")
            msg = get_text(
                lang, "confirm_transfer", req.channel,
                amount=fmt_amount(amt), beneficiary=ben, to_phone=to_phone,
                fee=fmt_amount(fee_val), total=fmt_amount(total_val),
            )
            return _build_response(
                req, lang, msg, Intent.CORRECTION,
                {"amount": amt, "beneficiary": ben, "fee": fee_val, "total": total_val, "currency": "XAF"},
                options=["Confirmer", "Annuler"],
                tx_id=session.pending_tx_id, tx_status=TransactionStatus.PENDING, started_at=t0,
            )

        # --- ACHAT DE CRÉDIT TÉLÉPHONIQUE ---
        if nlu.intent == Intent.AIRTIME_PURCHASE:
            session.draft_op_type = "airtime"
            amt = nlu.parameters.get("amount") or session.draft_transfer.get("amount")
            operator = nlu.parameters.get("operator") or session.draft_transfer.get("operator")
            to_phone = nlu.parameters.get("to_phone") or session.draft_transfer.get("to_phone") or phone
            if amt:
                session.draft_transfer["amount"] = amt
            if operator:
                session.draft_transfer["operator"] = operator
            if nlu.parameters.get("to_phone"):
                session.draft_transfer["to_phone"] = to_phone
            if not amt:
                session.awaiting_field = "amount"
                msg = get_text(lang, "ask_amount", req.channel)
                return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"operator": operator or "auto"}, started_at=t0)

            tx_payload: dict[str, Any] = {"type": "airtime", "from": phone, "to": to_phone, "amount": amt}
            if operator:
                tx_payload["operator"] = operator
            tx = await bank_client.create_transaction(tx_payload, trace_id, base_url)
            tx_id = tx.get("id") or tx.get("transaction_id")
            amt_val = tx.get("amount") if tx.get("amount") is not None else amt
            resolved_op = tx.get("operator") or operator or "MTN"
            fee_val = tx.get("fee") if tx.get("fee") is not None else 0
            session.pending_tx_id = tx_id
            session.pending_tx_trace_id = trace_id
            session.pending_op = {"type": "airtime", "amount": amt_val, "to": to_phone, "operator": resolved_op}
            session.awaiting_field = None
            session.draft_op_type = None
            session.draft_transfer = {}
            msg = get_text(
                lang, "confirm_airtime", req.channel,
                operator=resolved_op, amount=fmt_amount(amt_val), to_phone=to_phone, fee=fmt_amount(fee_val),
            )
            return _build_response(
                req, lang, msg, Intent.AIRTIME_PURCHASE,
                {"amount": amt_val, "operator": resolved_op, "to": to_phone, "fee": fee_val, "currency": "XAF"},
                options=["Confirmer", "Annuler"],
                tx_id=tx_id, tx_status=TransactionStatus.PENDING, started_at=t0,
            )

        # --- PAIEMENT DE FACTURE ---
        if nlu.intent == Intent.BILL_PAYMENT:
            session.draft_op_type = "bill"
            amt = nlu.parameters.get("amount") or session.draft_transfer.get("amount")
            biller = nlu.parameters.get("biller") or session.draft_transfer.get("biller") or "ENEO"
            if amt:
                session.draft_transfer["amount"] = amt
            session.draft_transfer["biller"] = biller
            if not amt:
                session.awaiting_field = "amount"
                msg = get_text(lang, "ask_amount", req.channel)
                return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"biller": biller}, started_at=t0)

            tx = await bank_client.create_transaction(
                {"type": "bill", "from": phone, "biller": biller, "amount": amt},
                trace_id, base_url,
            )
            tx_id = tx.get("id") or tx.get("transaction_id")
            amt_val = tx.get("amount") if tx.get("amount") is not None else amt
            fee_val = tx.get("fee") if tx.get("fee") is not None else 0
            total_val = tx.get("total") if tx.get("total") is not None else (amt_val + fee_val)
            session.pending_tx_id = tx_id
            session.pending_tx_trace_id = trace_id
            session.pending_op = {"type": "bill", "amount": amt_val, "biller": biller}
            session.awaiting_field = None
            session.draft_op_type = None
            session.draft_transfer = {}
            msg = get_text(
                lang, "confirm_bill", req.channel,
                biller=biller, amount=fmt_amount(amt_val), fee=fmt_amount(fee_val), total=fmt_amount(total_val),
            )
            return _build_response(
                req, lang, msg, Intent.BILL_PAYMENT,
                {"amount": amt_val, "biller": biller, "fee": fee_val, "total": total_val, "currency": "XAF"},
                options=["Confirmer", "Annuler"],
                tx_id=tx_id, tx_status=TransactionStatus.PENDING, started_at=t0,
            )

        # --- TRANSFERT D'ARGENT (TOUR 1 : INITIATION + RÉCAPITULATIF) ---
        if nlu.intent == Intent.TRANSFER:
            session.draft_op_type = "transfer"
            cand_idx = nlu.parameters.get("candidate_index")
            if cand_idx is not None and session.candidate_choices and 0 <= cand_idx < len(session.candidate_choices):
                chosen = session.candidate_choices[cand_idx]
                session.draft_transfer["to_phone"] = chosen.get("phone")
                session.draft_transfer["beneficiary"] = chosen.get("name") or chosen.get("phone")
                session.candidate_choices = []
                session.awaiting_field = None

            amt = nlu.parameters.get("amount") or session.draft_transfer.get("amount")
            to_phone = nlu.parameters.get("to_phone") or session.draft_transfer.get("to_phone")
            ben_name = nlu.parameters.get("beneficiary") or session.draft_transfer.get("beneficiary")

            if amt:
                session.draft_transfer["amount"] = amt
            if to_phone:
                session.draft_transfer["to_phone"] = to_phone
            if ben_name:
                session.draft_transfer["beneficiary"] = ben_name

            if not amt and not (to_phone or ben_name):
                session.awaiting_field = "amount"
                msg = get_text(lang, "ask_transfer_details", req.channel)
                return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, started_at=t0)
            if not amt:
                session.awaiting_field = "amount"
                msg = get_text(lang, "ask_amount", req.channel)
                return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, started_at=t0)
            if not (to_phone or ben_name):
                session.awaiting_field = "beneficiary"
                msg = get_text(lang, "ask_beneficiary", req.channel, amount=fmt_amount(amt))
                return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"amount": amt}, started_at=t0)

            resolved_name = ben_name or to_phone
            if not to_phone and ben_name:
                ben_res = await bank_client.search_beneficiaries(ben_name, None, trace_id, base_url)
                cands = ben_res.get("beneficiaries") or ben_res.get("candidates") or ben_res.get("data") or []
                if len(cands) == 0:
                    msg = get_error_text(lang, "UNKNOWN_BENEFICIARY")
                    return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"beneficiary": ben_name}, started_at=t0)
                if len(cands) > 1:
                    session.candidate_choices = cands[:3]
                    session.awaiting_field = "candidate_choice"
                    cand_opts = [f"{c.get('name')} ({c.get('phone')})" for c in session.candidate_choices]
                    cand_str = ", ".join(f"{i+1}.{c.get('name')} ({c.get('phone')})" for i, c in enumerate(session.candidate_choices))
                    msg = get_text(lang, "ask_clarify_candidates", req.channel, candidates=cand_str)
                    return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"candidates": cands}, options=cand_opts, started_at=t0)
                to_phone = cands[0].get("phone")
                resolved_name = cands[0].get("name") or to_phone

            tx = await bank_client.create_transaction(
                {"type": "transfer", "from": phone, "to": to_phone, "amount": amt},
                trace_id, base_url,
            )
            tx_id = tx.get("id") or tx.get("transaction_id")
            amt_val = tx.get("amount") if tx.get("amount") is not None else amt
            fee_val = tx.get("fee") if tx.get("fee") is not None else 0
            total_val = tx.get("total") if tx.get("total") is not None else (amt_val + fee_val)
            session.pending_tx_id = tx_id
            session.pending_tx_trace_id = trace_id
            session.pending_op = {"type": "transfer", "amount": amt_val, "to": to_phone, "beneficiary": resolved_name}
            session.awaiting_field = None
            session.draft_op_type = None
            session.draft_transfer = {}

            msg = get_text(
                lang, "confirm_transfer", req.channel,
                amount=fmt_amount(amt_val), beneficiary=resolved_name, to_phone=to_phone,
                fee=fmt_amount(fee_val), total=fmt_amount(total_val),
            )
            return _build_response(
                req, lang, msg, Intent.TRANSFER,
                {"amount": amt_val, "beneficiary": resolved_name, "to": to_phone, "fee": fee_val, "total": total_val, "currency": "XAF"},
                options=["Confirmer", "Annuler"],
                tx_id=tx_id, tx_status=TransactionStatus.PENDING, started_at=t0,
            )

        # --- MENU / INCONNU ---
        menu_opts = ["Solde", "Transfert", "Frais", "Historique", "Credit", "Facture"]
        if nlu.parameters.get("menu"):
            msg = get_text(lang, "menu", req.channel)
            return _build_response(req, lang, msg, Intent.UNKNOWN, options=menu_opts, started_at=t0)

        msg = get_text(lang, "unknown", req.channel)
        return _build_response(req, lang, msg, Intent.UNKNOWN, options=menu_opts, started_at=t0)

    except BankApiError as err:
        if err.code == "UNKNOWN_BENEFICIARY" and err.candidates:
            session.candidate_choices = err.candidates[:3]
            session.awaiting_field = "candidate_choice"
            session.draft_op_type = "transfer"
            cand_opts = [f"{c.get('name')} ({c.get('phone')})" for c in session.candidate_choices]
            cand_str = ", ".join(f"{i+1}.{c.get('name', c.get('phone', ''))}" for i, c in enumerate(session.candidate_choices))
            msg = get_text(lang, "ask_clarify_candidates", req.channel, candidates=cand_str)
            return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"error_code": err.code, "candidates": err.candidates}, options=cand_opts, started_at=t0)
        msg = get_error_text(lang, err.code)
        return _build_response(
            req, lang, msg, nlu.intent,
            {"error_code": err.code},
            tx_status=TransactionStatus.FAILED,
            started_at=t0,
        )


@app.get("/studio", response_class=HTMLResponse)
async def translate_studio() -> str:
    """Environnement web complet similaire à Google Traduction + Audio Lab + Simulateur Sandbox USSD & Mobile/Web."""
    src_lang_options = "".join(
        f'<option value="{code}">{label} ({code})</option>'
        for code, label in SUPPORTED_LANGUAGES.items()
    )
    tgt_lang_options = "".join(
        f'<option value="{code}" {"selected" if code == "dua" else ""}>{label} ({code})</option>'
        for code, label in CAMEROON_NATIONAL_LANGUAGES.items()
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Safinum Lingua Studio — Traduction Bancaire &amp; Audio Lab (Dev space ICT)</title>
<style>
  :root {{
    --bg: #0b1120; --panel: #111827; --panel2: #1e293b; --border: #334155;
    --text: #f8fafc; --muted: #94a3b8; --accent: #10b981; --accent2: #38bdf8;
    --warn: #f59e0b; --danger: #ef4444;
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0; }}
  header {{ background: #0f172a; border-bottom: 1px solid var(--border); padding: 14px 28px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }}
  .brand {{ display: flex; align-items: center; gap: 12px; }}
  .brand-logo {{ width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #10b981, #0ea5e9); display: flex; align-items: center; justify-content: center; font-weight: 800; color: #0b1120; font-size: 18px; }}
  .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .tab-btn {{ background: var(--panel2); color: var(--text); border: 1px solid var(--border); padding: 8px 16px; border-radius: 999px; cursor: pointer; font-size: 13px; font-weight: 600; transition: 0.15s; }}
  .tab-btn.active {{ background: var(--accent); color: #0b1120; border-color: var(--accent); }}
  .container {{ max-width: 1360px; margin: 0 auto; padding: 24px; }}
  .tab-pane {{ display: none; }}
  .tab-pane.active {{ display: block; }}
  .gt-bar {{ display: grid; grid-template-columns: 1fr auto 1fr; gap: 12px; align-items: center; background: var(--panel); border: 1px solid var(--border); border-radius: 14px 14px 0 0; padding: 12px 16px; }}
  .gt-grid {{ display: grid; grid-template-columns: 1fr 1fr; border: 1px solid var(--border); border-top: none; border-radius: 0 0 14px 14px; overflow: hidden; background: var(--panel); }}
  @media (max-width: 860px) {{ .gt-grid {{ grid-template-columns: 1fr; }} }}
  .gt-box {{ padding: 18px; display: flex; flex-direction: column; min-height: 280px; position: relative; }}
  .gt-box:first-child {{ border-right: 1px solid var(--border); }}
  textarea.gt-input {{ width: 100%; flex: 1; background: transparent; border: none; color: var(--text); font-size: 20px; line-height: 1.5; resize: none; outline: none; font-family: inherit; }}
  .gt-output {{ flex: 1; font-size: 22px; line-height: 1.5; color: #6ee7b7; font-weight: 500; white-space: pre-wrap; }}
  select, input[type="text"] {{ background: var(--panel2); color: var(--text); border: 1px solid var(--border); padding: 9px 12px; border-radius: 8px; font-size: 14px; outline: none; }}
  .btn {{ background: var(--accent); color: #0b1120; border: none; padding: 9px 16px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 13px; display: inline-flex; align-items: center; gap: 6px; }}
  .btn.secondary {{ background: var(--panel2); color: var(--text); border: 1px solid var(--border); }}
  .btn.blue {{ background: var(--accent2); color: #0b1120; }}
  .gt-footer {{ display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid #1f2937; margin-top: 12px; flex-wrap: wrap; gap: 8px; }}
  .pill {{ display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: #064e3b; color: #6ee7b7; }}
  .pill.warn {{ background: #78350f; color: #fcd34d; }}
  .pill.blue {{ background: #0c4a6e; color: #7dd3fc; }}
  .phonetic-card {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 12px; margin-top: 12px; font-size: 13px; line-height: 1.6; }}
  .presets {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
  .preset-chip {{ background: var(--panel); border: 1px solid var(--border); color: var(--muted); padding: 6px 12px; border-radius: 999px; font-size: 12px; cursor: pointer; }}
  .preset-chip:hover {{ border-color: var(--accent); color: var(--text); }}
  .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 14px; margin-top: 18px; }}
  .lang-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px; }}
  .lang-card h4 {{ margin: 0 0 6px; font-size: 14px; color: var(--accent2); display: flex; justify-content: space-between; align-items: center; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--panel); border-radius: 12px; overflow: hidden; font-size: 13px; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #1f2937; }}
  th {{ background: var(--panel2); color: var(--muted); }}
  code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #38bdf8; font-size: 12px; }}
  .ussd-layout {{ display: grid; grid-template-columns: 360px 1fr; gap: 24px; align-items: start; }}
  @media (max-width: 860px) {{ .ussd-layout {{ grid-template-columns: 1fr; }} }}
  .phone-frame {{ background: #0f172a; border: 4px solid #334155; border-radius: 28px; padding: 18px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }}
  .phone-screen {{ background: #022c22; color: #6ee7b7; font-family: monospace; font-size: 14px; min-height: 190px; border-radius: 12px; padding: 14px; white-space: pre-wrap; margin-bottom: 12px; border: 1px solid #065f46; }}
  .keypad {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }}
  .key-btn {{ background: #1e293b; color: #fff; border: 1px solid #334155; border-radius: 8px; padding: 11px; font-size: 16px; font-family: monospace; cursor: pointer; }}
  .key-btn:hover {{ background: #334155; }}
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="brand-logo">SL</div>
    <div>
      <div style="font-weight:800;font-size:17px;">Safinum Lingua Studio <span style="color:var(--accent);font-size:13px;">• Dev space ICT</span></div>
      <div style="font-size:12px;color:var(--muted);">Traducteur Bancaire IA (style Google Traduction) • Audio &amp; Phonétique • Simulateur Sandbox USSD &amp; Mobile/Web</div>
    </div>
  </div>
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('gt', this)">🌐 Google Traduction &amp; Audio Auto</button>
    <button class="tab-btn" onclick="switchTab('all9', this)">📊 7 Langues Camerounaises (incl. Pidgin)</button>
    <button class="tab-btn" onclick="switchTab('scenarios', this)">🏆 10 Scénarios Jury &amp; Sandbox</button>
    <button class="tab-btn" onclick="switchTab('uikeys', this)">📱 89 Clés UI Mobile/Web</button>
    <button class="tab-btn" onclick="switchTab('native', this)">🎙️ 11 Audio Locuteurs Natifs (Homme)</button>
    <button class="tab-btn" onclick="switchTab('ussd', this)">📟 Testeur USSD (*123#)</button>
    <a href="/" class="tab-btn" style="text-decoration:none;">📈 Diagnostics Jury</a>
  </div>
</header>

<div class="container">
  <!-- ONGLET 1 : GOOGLE TRADUCTION & AUDIO LAB -->
  <div id="tab-gt" class="tab-pane active">
    <div class="presets">
      <span style="font-size:12px;color:var(--muted);align-self:center;">Exemples rapides (avec protection bancaire) :</span>
      <button class="preset-chip" onclick="setSource('Bonjour Amina, envoyer 15 000 FCFA à Jean Mbarga au 677000002')">Transfert + Nom + Téléphone</button>
      <button class="preset-chip" onclick="setSource('Quel est mon solde disponible ?')">Consultation de solde</button>
      <button class="preset-chip" onclick="setSource('Solde insuffisant pour payer la facture ENEO de 25 000 FCFA (Réf TRX-9042)')">Solde insuffisant + ENEO + Réf</button>
      <button class="preset-chip" onclick="setSource('confirmer')">Mot isolé : Confirmer</button>
      <button class="preset-chip" onclick="setSource('bénéficiaire')">Mot isolé : Bénéficiaire</button>
      <button class="preset-chip" onclick="setSource('Merci beaucoup')">Merci beaucoup</button>
    </div>

    <div class="gt-bar">
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:13px;color:var(--muted);">Source :</span>
        <select id="srcLang" onchange="runTranslate()">
          <option value="" selected>Détection automatique</option>
          {src_lang_options}
        </select>
        <span id="detectedBadge" class="pill blue">Auto</span>
      </div>
      <button class="btn secondary" onclick="swapLanguages()" title="Inverser les langues">⇄</button>
      <div style="display:flex;align-items:center;gap:10px;justify-content:flex-end;">
        <span style="font-size:13px;color:var(--muted);">Langue cible :</span>
        <select id="tgtLang" onchange="runTranslate()">
          {tgt_lang_options}
        </select>
      </div>
    </div>

    <div class="gt-grid">
      <!-- Boîte Source -->
      <div class="gt-box">
        <textarea id="srcText" class="gt-input" oninput="debouncedTranslate()" placeholder="Saisissez un mot, une phrase bancaire, un montant en FCFA, un nom de client...">Bonjour Amina, envoyer 15 000 FCFA à Jean Mbarga au 677000002</textarea>
        <div class="gt-footer">
          <div style="display:flex;gap:8px;align-items:center;">
            <button class="btn secondary" onclick="dictateSource()" id="micBtn">🎤 Dicter</button>
            <button class="btn secondary" onclick="speakText(document.getElementById('srcText').value, document.getElementById('srcLang').value || 'fr')">🔊 Écouter source</button>
          </div>
          <div id="protectedPills" style="display:flex;gap:6px;flex-wrap:wrap;"></div>
        </div>
      </div>

      <!-- Boîte Traduction & Audio -->
      <div class="gt-box">
        <div id="outText" class="gt-output">Chargement...</div>
        <div class="phonetic-card" id="phoneticCard">
          <div><b>Transcription API / IPA :</b> <code id="ipaOut">/.../</code></div>
          <div><b>Script vocal TTS (adapté prononciation) :</b> <span id="ttsScriptOut" style="color:#fcd34d;">...</span></div>
          <div><b>Aperçu USSD GSM-7 (max 182 septets) :</b> <code id="gsmOut">...</code> <span id="gsmCount" class="pill">0/182</span></div>
        </div>
        <div class="gt-footer">
          <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
            <button class="btn blue" onclick="playTargetAudio()">🔊 Réécouter (Voix Homme)</button>
            <button class="btn secondary" onclick="copyTranslation()">📋 Copier</button>
            <label style="font-size:12px;color:#6ee7b7;display:flex;align-items:center;gap:4px;font-weight:600;">
              <input type="checkbox" id="autoSpeakToggle" checked> 🔊 Voix auto à chaque texte
            </label>
            <label style="font-size:12px;color:var(--muted);display:flex;align-items:center;gap:4px;">
              Vitesse: <input type="range" id="ttsRate" min="0.6" max="1.3" step="0.05" value="0.95" style="width:70px;">
            </label>
          </div>
          <span id="modeBadge" class="pill">mode</span>
        </div>
        <div style="margin-top:10px;display:flex;align-items:center;gap:10px;background:#0f172a;padding:8px 12px;border-radius:8px;border:1px solid #1e293b;">
          <span style="font-size:12px;color:#6ee7b7;font-weight:600;">🎙️ Audio WAV Homme généré automatiquement :</span>
          <audio id="autoWavPlayer" controls style="height:30px;flex:1;"></audio>
        </div>
      </div>
    </div>
  </div>

  <!-- ONGLET SCÉNARIOS JURY & SANDBOX -->
  <div id="tab-scenarios" class="tab-pane">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
      <div>
        <h3 style="margin:0;">🏆 Les 10 Scénarios Officiels du Jury SAFINUM 2026 (Exécution Live + Voix Homme Auto)</h3>
        <p style="margin:4px 0 0;font-size:13px;color:var(--muted);">Cliquez sur chaque étape pour jouer le scénario réel sur <code>POST /middleware</code> : la réponse s'affiche et la voix masculine lit automatiquement le résultat.</p>
      </div>
    </div>
    <div id="scenariosGrid" class="cards-grid" style="grid-template-columns:repeat(auto-fill,minmax(400px,1fr));"></div>
  </div>

  <!-- ONGLET 2 : COMPARATEUR 7 LANGUES CAMEROUNAISES -->
  <div id="tab-all9" class="tab-pane">
    <div style="display:flex;gap:12px;align-items:center;margin-bottom:16px;">
      <input type="text" id="all9Input" value="Bonjour Amina, envoyer 5 000 FCFA à Jean Mbarga au 677000001" style="flex:1;font-size:15px;">
      <button class="btn" onclick="runTranslateAll9()">Traduire dans toutes les langues camerounaises</button>
    </div>
    <div id="all9Grid" class="cards-grid"></div>
  </div>

  <!-- ONGLET 3 : 89 CLÉS UI MOBILE & WEB -->
  <div id="tab-uikeys" class="tab-pane">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
      <div>
        <h3 style="margin:0;">Inspection &amp; Test Audio des 89 Clés UI (Contrat Mobile &amp; Web `ui_translation`)</h3>
        <p style="margin:4px 0 0;font-size:13px;color:var(--muted);">Vérifiez que chaque <code>{{placeholder}}</code> (<code>{{amount}}</code>, <code>{{name}}</code>, <code>{{phone}}</code>, <code>{{fee}}</code>, <code>{{max}}</code>, <code>{{missing}}</code>) est 100% intact et écoutez chaque clé.</p>
      </div>
      <div style="display:flex;gap:10px;align-items:center;">
        <select id="uiKeysLang" onchange="loadUiKeys()">{tgt_lang_options}</select>
        <input type="text" id="uiKeysFilter" placeholder="Filtrer clé ou texte..." oninput="filterUiKeysTable()">
      </div>
    </div>
    <table>
      <thead><tr><th>Clé officielle</th><th>Source (Français)</th><th>Traduction affichée</th><th>Phonétique IPA</th><th>Audio</th></tr></thead>
      <tbody id="uiKeysBody"></tbody>
    </table>
  </div>

  <!-- ONGLET 4 : BANQUE VOCALE NATIVE SOREVA (1 050 CLIPS) + LINGUA LIBRE -->
  <div id="tab-native" class="tab-pane">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:14px;">
      <div>
        <h3 style="margin:0 0 4px;">1. Banque Vocale Native SOREVA (1 050 clips • 150 phrases × 7 langues camerounaises • Voix Homme ElevenLabs STS)</h3>
        <p style="margin:0;font-size:13px;color:var(--muted);">Prononciation, tons et prosodie authentiques de locuteurs natifs (Goethe-Institut / CC-BY-4.0), convertis en voix d'homme grave unique (Brian ~110 Hz via Speech-to-Speech).</p>
      </div>
      <div style="display:flex;gap:10px;align-items:center;">
        <select id="sorevaLangSelect" onchange="loadSorevaBank()">{tgt_lang_options}</select>
        <span id="sorevaCountBadge" class="pill">150 clips</span>
      </div>
    </div>
    <table style="margin-bottom:24px;">
      <thead><tr><th>Clip SOREVA</th><th>Orthographe AGLC (tons)</th><th>Texte simplifié</th><th>Écouter (Voix Homme Native STS)</th></tr></thead>
      <tbody id="sorevaBody"></tbody>
    </table>

    <h3 style="margin:0 0 6px;">2. Enregistrements Masculins Vérifiés (Lingua Libre / Wikimedia Commons)</h3>
    <p style="margin:0 0 16px;font-size:13px;color:var(--muted);">11 enregistrements masculins vérifiés (105–143 Hz) en Ewondo, Fulfulde et Pidgin.</p>
    <table>
      <thead><tr><th>Langue</th><th>Sens (FR)</th><th>Fichier</th><th>Locuteur / Source</th><th>Licence</th><th>Écoute directe</th></tr></thead>
      <tbody id="nativeBody"></tbody>
    </table>
  </div>

  <!-- ONGLET 5 : SIMULATEUR USSD LOCAL (*123#) -->
  <div id="tab-ussd" class="tab-pane">
    <div class="ussd-layout">
      <div class="phone-frame">
        <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-bottom:8px;">
          <span>Safinum Telecom • GSM-7</span><span>*123#</span>
        </div>
        <div class="phone-screen" id="ussdScreen">Composez *123# ou cliquez sur Envoyer pour démarrer.</div>
        <div id="ussdOptions" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;"></div>
        <input type="text" id="ussdInput" value="*123#" style="width:100%;text-align:center;font-family:monospace;font-size:15px;margin-bottom:8px;" onkeydown="if(event.key==='Enter')sendUssd()">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
          <button class="btn" style="justify-content:center;" onclick="sendUssd()">📞 Envoyer</button>
          <button class="btn secondary" style="justify-content:center;" onclick="resetUssd()">🔄 Nouvelle session</button>
        </div>
        <div class="keypad">
          <button class="key-btn" onclick="pressKey('1')">1</button>
          <button class="key-btn" onclick="pressKey('2')">2</button>
          <button class="key-btn" onclick="pressKey('3')">3</button>
          <button class="key-btn" onclick="pressKey('4')">4</button>
          <button class="key-btn" onclick="pressKey('5')">5</button>
          <button class="key-btn" onclick="pressKey('6')">6</button>
          <button class="key-btn" onclick="pressKey('7')">7</button>
          <button class="key-btn" onclick="pressKey('8')">8</button>
          <button class="key-btn" onclick="pressKey('9')">9</button>
          <button class="key-btn" onclick="pressKey('*')">*</button>
          <button class="key-btn" onclick="pressKey('0')">0</button>
          <button class="key-btn" onclick="pressKey('#')">#</button>
        </div>
      </div>
      <div>
        <div style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;">
          <h3 style="margin:0 0 12px;">Paramètres de la session USSD</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <label style="font-size:12px;color:var(--muted);display:block;margin-bottom:4px;">Numéro de compte</label>
              <input type="text" id="ussdPhone" value="237677000001" style="width:100%;">
            </div>
            <div>
              <label style="font-size:12px;color:var(--muted);display:block;margin-bottom:4px;">Langue de session</label>
              <select id="ussdLang" style="width:100%;">
                <option value="" selected>Auto-détection (null)</option>
                {src_lang_options}
              </select>
            </div>
          </div>
          <div style="margin-top:16px;">
            <h4 style="margin:0 0 8px;font-size:13px;color:var(--muted);">Réponse JSON complète (`POST /middleware`) :</h4>
            <pre id="ussdJson" style="background:#0f172a;padding:12px;border-radius:8px;font-size:12px;overflow-x:auto;color:#7dd3fc;margin:0;">En attente...</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
let currentTr = {{}};
let debounceTimer = null;
let allUiItems = [];

function switchTab(id, btn) {{
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  btn.classList.add('active');
  if (id === 'all9') runTranslateAll9();
  if (id === 'scenarios') loadJuryScenarios();
  if (id === 'uikeys' && !allUiItems.length) loadUiKeys();
  if (id === 'native') loadNativeRecordings();
}}

function setSource(txt) {{
  document.getElementById('srcText').value = txt;
  runTranslate();
}}

function swapLanguages() {{
  const s = document.getElementById('srcLang');
  const t = document.getElementById('tgtLang');
  const oldT = t.value;
  t.value = s.value || 'fr';
  s.value = oldT;
  if (currentTr.translated) {{
    document.getElementById('srcText').value = currentTr.translated;
  }}
  runTranslate();
}}

function debouncedTranslate() {{
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => runTranslate(true), 420);
}}

let lastAutoSpokenKey = "";
async function runTranslate(fromTyping = false) {{
  const text = document.getElementById('srcText').value;
  const srcLang = document.getElementById('srcLang').value;
  const tgtLang = document.getElementById('tgtLang').value;
  const r = await fetch('/api/translate', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ text, source_language: srcLang, language: tgtLang }})
  }});
  const d = await r.json();
  currentTr = d;
  document.getElementById('outText').innerText = d.translated || '';
  document.getElementById('detectedBadge').innerText = 'Source: ' + (d.source_language || 'fr');
  document.getElementById('modeBadge').innerText = 'Moteur: ' + (d.mode || 'local');
  document.getElementById('ipaOut').innerText = d.ipa || '';
  document.getElementById('ttsScriptOut').innerText = (d.tts_engine === 'elevenlabs-male' && d.elevenlabs_native_text) ? d.elevenlabs_native_text : (d.tts_script || '');
  document.getElementById('gsmOut').innerText = d.gsm7_preview || '';
  const septets = (d.gsm_meta && d.gsm_meta.septets) || 0;
  document.getElementById('gsmCount').innerText = septets + '/182 septets';
  const protDiv = document.getElementById('protectedPills');
  const ents = d.protected_entities || [];
  protDiv.innerHTML = ents.length
    ? ents.map(e => `<span class="pill warn" title="Protégé contre toute altération">🔒 ${{e}}</span>`).join('')
    : '<span style="font-size:12px;color:var(--muted);">🔒 Chiffres &amp; noms protégés</span>';

  // Mise à jour automatique de l'unique lecteur WAV Homme en fonction du texte et de la langue
  if (d.translated) {{
    const wavUrl = `/api/audio/tts?text=${{encodeURIComponent(d.translated)}}&language=${{encodeURIComponent(tgtLang)}}`;
    const player = document.getElementById('autoWavPlayer');
    const speakKey = `${{tgtLang}}:${{d.translated}}`;
    if (player && player.dataset.srcKey !== speakKey) {{
      player.pause();
      player.dataset.srcKey = speakKey;
      player.src = wavUrl;
    }}
    const autoOn = document.getElementById('autoSpeakToggle')?.checked;
    if (autoOn && speakKey !== lastAutoSpokenKey) {{
      lastAutoSpokenKey = speakKey;
      playTargetAudio();
    }}
  }}
}}

let currentWavPlayer = null;
function stopAllAudio() {{
  if ('speechSynthesis' in window) {{
    window.speechSynthesis.cancel();
  }}
  if (currentWavPlayer) {{
    currentWavPlayer.pause();
    currentWavPlayer.currentTime = 0;
    currentWavPlayer = null;
  }}
  const domPlayer = document.getElementById('autoWavPlayer');
  if (domPlayer && !domPlayer.paused) {{
    domPlayer.pause();
    domPlayer.currentTime = 0;
  }}
}}

function speakText(text, lang, ttsScript) {{
  if (!text) return;
  stopAllAudio();
  const rate = parseFloat(document.getElementById('ttsRate')?.value || '0.95');
  const url = `/api/audio/tts?text=${{encodeURIComponent(text)}}&language=${{encodeURIComponent(lang || 'fr')}}`;
  const audio = new Audio(url);
  audio.playbackRate = rate;
  currentWavPlayer = audio;
  audio.play().catch(() => {{}});
}}

async function playTargetAudio() {{
  if (!currentTr.translated) return;
  stopAllAudio();
  const lang = document.getElementById('tgtLang').value;
  const rate = parseFloat(document.getElementById('ttsRate')?.value || '0.95');
  const domPlayer = document.getElementById('autoWavPlayer');
  if (domPlayer) {{
    const wavUrl = `/api/audio/tts?text=${{encodeURIComponent(currentTr.translated)}}&language=${{encodeURIComponent(lang)}}`;
    const speakKey = `${{lang}}:${{currentTr.translated}}`;
    if (domPlayer.dataset.srcKey !== speakKey) {{
      domPlayer.dataset.srcKey = speakKey;
      domPlayer.src = wavUrl;
    }}
    domPlayer.playbackRate = rate;
    domPlayer.currentTime = 0;
    domPlayer.play().catch(() => {{}});
    return;
  }}
  speakText(currentTr.translated, lang, currentTr.tts_script);
}}

function copyTranslation() {{
  if (!currentTr.translated) return;
  navigator.clipboard.writeText(currentTr.translated);
}}

function dictateSource() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{ alert("Reconnaissance vocale non supportée sur ce navigateur."); return; }}
  const rec = new SR();
  rec.lang = 'fr-FR';
  rec.onresult = (e) => {{
    document.getElementById('srcText').value = e.results[0][0].transcript;
    runTranslate();
  }};
  rec.start();
}}

async function runTranslateAll9() {{
  const text = document.getElementById('all9Input').value;
  const r = await fetch('/api/translate-all', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ text }})
  }});
  const d = await r.json();
  const grid = document.getElementById('all9Grid');
  grid.innerHTML = Object.entries(d.translations).map(([code, item]) => `
    <div class="lang-card">
      <h4><span>${{item.label}} (<code>${{code}}</code>)</span> <span class="pill">${{item.gsm7_septets}}/182</span></h4>
      <div style="font-size:17px;color:#6ee7b7;font-weight:600;margin:8px 0;">${{item.translated}}</div>
      <div style="font-size:12px;color:var(--muted);"><b>IPA:</b> <code>${{item.ipa}}</code></div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:10px;"><b>TTS:</b> ${{item.tts_script}}</div>
      <button class="btn secondary" onclick="speakText(${{JSON.stringify(item.translated)}}, '${{code}}', ${{JSON.stringify(item.tts_script)}})">🔊 Écouter</button>
    </div>
  `).join('');
}}

async function loadUiKeys() {{
  const lang = document.getElementById('uiKeysLang').value;
  const r = await fetch(`/api/ui-keys?language=${{encodeURIComponent(lang)}}`);
  const d = await r.json();
  allUiItems = d.items || [];
  renderUiKeys(allUiItems, lang);
}}

function renderUiKeys(items, lang) {{
  const tbody = document.getElementById('uiKeysBody');
  tbody.innerHTML = items.map(x => `
    <tr>
      <td><code>${{x.key}}</code></td>
      <td style="color:var(--muted);">${{x.source_fr}}</td>
      <td style="color:#6ee7b7;font-weight:600;">${{x.translated}}</td>
      <td><code>${{x.ipa}}</code></td>
      <td><button class="btn secondary" style="padding:5px 10px;" onclick='speakText(${{JSON.stringify(x.translated)}}, "${{lang}}", ${{JSON.stringify(x.tts_script)}})'>🔊</button></td>
    </tr>
  `).join('');
}}

function filterUiKeysTable() {{
  const q = document.getElementById('uiKeysFilter').value.toLowerCase();
  const lang = document.getElementById('uiKeysLang').value;
  const filtered = allUiItems.filter(x => x.key.toLowerCase().includes(q) || x.source_fr.toLowerCase().includes(q) || x.translated.toLowerCase().includes(q));
  renderUiKeys(filtered, lang);
}}

async function loadSorevaBank() {{
  const sel = document.getElementById('sorevaLangSelect');
  const lang = sel ? sel.value : 'ewo';
  const r = await fetch(`/api/native-bank?language=${{encodeURIComponent(lang)}}`);
  const d = await r.json();
  const badge = document.getElementById('sorevaCountBadge');
  if (badge) badge.innerText = `${{d.count || 0}} clips (${{lang}})`;
  const tbody = document.getElementById('sorevaBody');
  if (!tbody) return;
  tbody.innerHTML = (d.items || []).slice(0, 60).map(x => `
    <tr>
      <td><code>${{x.clip}}</code></td>
      <td style="color:#6ee7b7;font-weight:600;">${{x.aglc}}</td>
      <td style="color:var(--muted);">${{x.plain}}</td>
      <td><button class="btn secondary" style="padding:5px 10px;" onclick='speakText(${{JSON.stringify(x.aglc)}}, "${{lang}}", ${{JSON.stringify(x.plain)}})'>🔊 Écouter (Voix Homme)</button></td>
    </tr>
  `).join('');
}}

async function loadNativeRecordings() {{
  loadSorevaBank();
  const r = await fetch('/api/native-recordings');
  const d = await r.json();
  const tbody = document.getElementById('nativeBody');
  tbody.innerHTML = (d.items || []).map(x => `
    <tr>
      <td><span class="pill blue">${{x.language}}</span></td>
      <td style="font-weight:600;">${{x.meaning_fr}}</td>
      <td><code>${{x.filename}}</code></td>
      <td style="font-size:12px;color:var(--muted);">${{x.speaker}}</td>
      <td><span class="pill">${{x.license}}</span></td>
      <td><audio controls preload="none" src="${{x.audio_url}}" style="height:32px;"></audio></td>
    </tr>
  `).join('');
}}

function pressKey(k) {{
  const inp = document.getElementById('ussdInput');
  inp.value += k;
}}

function resetUssd() {{
  document.getElementById('ussdInput').value = '*123#';
  sendUssd();
}}

async function sendUssd(customText) {{
  const inp = document.getElementById('ussdInput');
  const text = customText !== undefined ? customText : inp.value;
  const phone = document.getElementById('ussdPhone').value;
  const lang = document.getElementById('ussdLang').value || null;
  inp.value = '';
  const r = await fetch('/middleware', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json', 'X-Trace-Id': 'studio-' + Date.now() }},
    body: JSON.stringify({{
      trace_id: 'studio-' + Date.now(),
      channel: 'ussd',
      phone: phone,
      language: lang,
      input: {{ type: 'menu', text: text }},
      constraints: {{ max_chars: 182, charset: 'gsm7', mode: 'menu', timeout_ms: 3000 }}
    }})
  }});
  const d = await r.json();
  const respText = (d.response && d.response.text) || '(vide)';
  document.getElementById('ussdScreen').innerText = respText;
  document.getElementById('ussdJson').innerText = JSON.stringify(d, null, 2);
  const opts = (d.response && d.response.options) || [];
  document.getElementById('ussdOptions').innerHTML = opts.map((o, idx) =>
    `<button class="preset-chip" onclick="sendUssd('${{idx+1}}')">${{idx+1}}. ${{o}}</button>`
  ).join('');
  // Lecture vocale automatique de la réponse USSD par la voix masculine
  const respLang = (d.interpretation && d.interpretation.language) || lang || 'fr';
  speakText(respText, respLang);
}}

let juryScenariosList = [];
async function loadJuryScenarios() {{
  const r = await fetch('/api/jury-scenarios');
  const d = await r.json();
  juryScenariosList = d.items || [];
  const grid = document.getElementById('scenariosGrid');
  grid.innerHTML = juryScenariosList.map((sc, sIdx) => `
    <div class="lang-card">
      <h4><span>${{sc.title}}</span> <span class="pill blue">${{sc.language || 'auto'}}</span></h4>
      <p style="font-size:12px;color:var(--muted);margin:6px 0 10px;">${{sc.description}}</p>
      <div style="display:flex;flex-direction:column;gap:6px;">
        ${{sc.steps.map((st, stIdx) => `
          <button class="btn secondary" style="justify-content:space-between;text-align:left;" onclick="runScenarioStep(${{sIdx}}, ${{stIdx}})">
            <span>▶ ${{st.label}} : <code>${{st.text}}</code></span>
            <span class="pill">${{st.channel}}</span>
          </button>
        `).join('')}}
      </div>
      <div id="sc-out-${{sIdx}}" style="margin-top:10px;font-size:12px;background:#0f172a;padding:10px;border-radius:8px;display:none;"></div>
    </div>
  `).join('');
}}

async function runScenarioStep(sIdx, stIdx) {{
  const sc = juryScenariosList[sIdx];
  const st = sc.steps[stIdx];
  const traceId = `jury-sc${{sc.id}}-step${{stIdx+1}}-${{Date.now()}}`;
  const r = await fetch('/middleware', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json', 'X-Trace-Id': traceId }},
    body: JSON.stringify({{
      trace_id: traceId,
      channel: st.channel,
      phone: '237677000001',
      language: st.language,
      input: {{ type: 'text', text: st.text }},
      constraints: {{ max_chars: 182, charset: 'gsm7', mode: 'menu', timeout_ms: 3000 }}
    }})
  }});
  const d = await r.json();
  const box = document.getElementById(`sc-out-${{sIdx}}`);
  box.style.display = 'block';
  const txt = (d.response && d.response.text) || '';
  const intent = (d.interpretation && d.interpretation.intent) || '';
  const lang = (d.interpretation && d.interpretation.language) || st.language || 'fr';
  const txSt = (d.transaction && d.transaction.status) || 'none';
  box.innerHTML = `
    <div><span class="pill">${{intent}}</span> <span class="pill blue">Lang: ${{lang}}</span> <span class="pill warn">Tx: ${{txSt}}</span></div>
    <div style="color:#6ee7b7;font-weight:600;margin-top:6px;white-space:pre-wrap;">${{txt}}</div>
  `;
  speakText(txt, lang);
}}

runTranslate();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    return """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Safinum Lingua — Diagnostics & Jury Dashboard</title>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; background: #0b1220; color: #e2e8f0; margin: 0; padding: 24px; }
  .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 24px; }
  .badge { background: #059669; color: #fff; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; }
  .card h3 { margin: 0 0 8px; font-size: 13px; color: #94a3b8; text-transform: uppercase; }
  .card .val { font-size: 24px; font-weight: 700; color: #10b981; }
  table { width: 100%; border-collapse: collapse; background: #111827; border-radius: 12px; overflow: hidden; }
  th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #1f2937; font-size: 13px; }
  th { background: #1e293b; color: #cbd5e1; }
  code { background: #1e293b; padding: 2px 6px; border-radius: 4px; color: #38bdf8; }
</style>
</head>
<body>
  <div class="header">
    <div>
      <h1 style="margin:0;font-size:22px;">Safinum Lingua — Infrastructure Linguistique Universelle</h1>
      <p style="margin:4px 0 0;color:#94a3b8;font-size:14px;">USSD Conversationnel + Mobile/Web UI Translation • Phonétique TTS • 9 Langues • GSM-7 Strict</p>
    </div>
    <div style="display:flex;gap:10px;align-items:center;">
      <a href="/studio" style="background:#38bdf8;color:#0b1220;padding:6px 14px;border-radius:999px;font-size:13px;font-weight:700;text-decoration:none;">🌐 Ouvrir Studio Traduction &amp; Audio</a>
      <span class="badge">LIVE DIAGNOSTICS</span>
    </div>
  </div>
  <div class="grid">
    <div class="card"><h3>Langues supportées</h3><div class="val">9</div><small>fr, en, ewo, fub, dua, bas, bbj, byv, wes</small></div>
    <div class="card"><h3>Contrats Sandbox</h3><div class="val">USSD + UI</div><small>USSD menu + Mobile/Web 89 clés</small></div>
    <div class="card"><h3>Conformité USSD</h3><div class="val">182 septets</div><small>Translittération GSM-7 automatique</small></div>
    <div class="card"><h3>Audio & Phonétique</h3><div class="val">IPA + TTS</div><small>Adaptation fr-FR + MMS-TTS local</small></div>
  </div>
  <table>
    <thead><tr><th>Trace ID</th><th>Canal</th><th>Mode</th><th>Langue</th><th>Intention / Écran</th><th>Limite</th><th>Latence</th><th>Réponse</th></tr></thead>
    <tbody id="rows"><tr><td colspan="8" style="color:#64748b;">En attente de requêtes sur POST /middleware...</td></tr></tbody>
  </table>
  <script>
    async function refresh() {
      const r = await fetch('/api/diagnostics');
      const d = await r.json();
      const tbody = document.getElementById('rows');
      if (!d.items.length) return;
      tbody.innerHTML = d.items.map(x => `<tr>
        <td><code>${x.trace_id}</code></td>
        <td>${x.channel}</td>
        <td>${x.mode || 'ussd'}</td>
        <td><code>${x.language}</code></td>
        <td><code>${x.intent}</code></td>
        <td>${x.gsm_meta.septets}/${x.gsm_meta.limit || '-'} (${x.gsm_meta.charset})</td>
        <td>${x.latency_ms} ms</td>
        <td>${x.response_preview}</td>
      </tr>`).join('');
    }
    setInterval(refresh, 2000);
    refresh();
  </script>
</body>
</html>"""
