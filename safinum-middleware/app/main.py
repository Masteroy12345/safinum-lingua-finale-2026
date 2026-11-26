"""Point d'entrée FastAPI de Safinum Lingua — Infrastructure Linguistique Universelle.

Gère les DEUX contrats officiels de la passerelle Safinum :
1. Canal USSD conversationnel (`input` -> réponse conversationnelle GSM-7 <= 182 septets + banque).
2. Canaux Mobile et Web (`type == "ui_translation"` -> traduction d'écrans JSON avec placeholders intacts & max_chars).
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .bank_client import BankApiError, BankClient
from .config import settings
from .gsm7 import fit_channel_constraints
from .languages import (
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
from .ui_translator import handle_ui_translation

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
    """Traduit un mot ou une phrase complète en protégeant montants/numéros, avec sortie IPA et audio."""
    text = payload.get("text", "")
    lang = normalize_language(payload.get("language")) or "fr"
    res = translate_phrase(text, lang)
    audio = build_audio_payload(res["translated"], lang)
    return {**res, **audio}


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

    try:
        # --- CHANGEMENT DE LANGUE ---
        if nlu.intent == Intent.LANGUAGE_SWITCH:
            target = nlu.parameters.get("target_language")
            if target and target in SUPPORTED_LANGUAGES:
                session.language = target
                msg = get_text(target, "lang_switched", req.channel)
                return _build_response(req, target, msg, Intent.LANGUAGE_SWITCH, {"language": target}, started_at=t0)
            opts = [f"{k}:{v}" for k, v in SUPPORTED_LANGUAGES.items()]
            msg = "Langues: " + ", ".join(f"{k}={v}" for k, v in SUPPORTED_LANGUAGES.items())
            return _build_response(req, lang, msg, Intent.LANGUAGE_SWITCH, {"available": list(SUPPORTED_LANGUAGES.keys())}, options=opts, started_at=t0)

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
                    cand_str = ", ".join(f"{c.get('name')} ({c.get('phone')})" for c in cands[:3])
                    msg = get_text(lang, "ask_clarify_candidates", req.channel, candidates=cand_str)
                    return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"candidates": cands}, started_at=t0)
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
        if nlu.parameters.get("menu"):
            msg = get_text(lang, "menu", req.channel)
            return _build_response(req, lang, msg, Intent.UNKNOWN, started_at=t0)

        msg = get_text(lang, "unknown", req.channel)
        return _build_response(req, lang, msg, Intent.UNKNOWN, started_at=t0)

    except BankApiError as err:
        if err.code == "UNKNOWN_BENEFICIARY" and err.candidates:
            cand_str = ", ".join(f"{c.get('name', c.get('phone', ''))}" for c in err.candidates[:3])
            msg = get_text(lang, "ask_clarify_candidates", req.channel, candidates=cand_str)
            return _build_response(req, lang, msg, Intent.CLARIFICATION_NEEDED, {"error_code": err.code}, started_at=t0)
        msg = get_error_text(lang, err.code)
        return _build_response(
            req, lang, msg, nlu.intent,
            {"error_code": err.code},
            tx_status=TransactionStatus.FAILED,
            started_at=t0,
        )


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
    <span class="badge">LIVE DIAGNOSTICS</span>
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
