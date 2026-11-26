"""Modèles Pydantic conformes au contrat Safinum Gateway (USSD conversationnel + Mobile/Web ui_translation)."""
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Intent(str, Enum):
    BALANCE_INQUIRY = "BALANCE_INQUIRY"
    TRANSFER = "TRANSFER"
    FEE_INQUIRY = "FEE_INQUIRY"
    TRANSACTION_HISTORY = "TRANSACTION_HISTORY"
    AIRTIME_PURCHASE = "AIRTIME_PURCHASE"
    BILL_PAYMENT = "BILL_PAYMENT"
    CONFIRM = "CONFIRM"
    CANCEL = "CANCEL"
    CORRECTION = "CORRECTION"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    TERM_EXPLANATION = "TERM_EXPLANATION"
    LANGUAGE_SWITCH = "LANGUAGE_SWITCH"
    UNKNOWN = "UNKNOWN"


class TransactionStatus(str, Enum):
    NONE = "none"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class GatewayInput(BaseModel):
    type: str = "text"  # "menu", "text", "keypad", "audio"
    text: Optional[str] = ""
    ussd_text: Optional[str] = None
    audio_base64: Optional[str] = None
    sample_rate: Optional[int] = None


class GatewayConstraints(BaseModel):
    max_chars: Optional[int] = None
    charset: Optional[str] = None
    mode: Optional[str] = None
    timeout_ms: Optional[int] = None


class BankApiInfo(BaseModel):
    base_url: Optional[str] = None


class GatewayRequest(BaseModel):
    trace_id: str
    team_id: Optional[str] = None
    channel: str = "ussd"  # ussd, mobile, web, sms, atm, ivr
    session_id: Optional[str] = None
    phone: str
    language: Optional[str] = None  # ISO 639-3 ou null
    input: GatewayInput = Field(default_factory=GatewayInput)
    constraints: GatewayConstraints = Field(default_factory=GatewayConstraints)
    bank_api: BankApiInfo = Field(default_factory=BankApiInfo)


class MiddlewareResponseBody(BaseModel):
    text: str
    end_session: bool = False
    # Ussd.js du simulateur mappe options via String(opt), donc liste de chaînes
    options: list[str] = Field(default_factory=list)


class InterpretationBody(BaseModel):
    intent: Intent
    parameters: dict[str, Any] = Field(default_factory=dict)
    language: str = "fr"


class TransactionBody(BaseModel):
    id: Optional[str] = None
    status: TransactionStatus = TransactionStatus.NONE


class GatewayResponse(BaseModel):
    response: MiddlewareResponseBody
    interpretation: InterpretationBody
    transaction: TransactionBody = Field(default_factory=TransactionBody)


class UIStringEntry(BaseModel):
    text: str
    context: Optional[str] = None
    max_chars: Optional[int] = None


class UITranslationRequest(BaseModel):
    trace_id: Optional[str] = None
    team_id: Optional[str] = None
    channel: str = "mobile"  # mobile | web
    type: str = "ui_translation"
    session_id: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None
    source_language: Optional[str] = "fr"
    screen: Optional[str] = "home"
    strings: dict[str, UIStringEntry] = Field(default_factory=dict)
    constraints: GatewayConstraints = Field(default_factory=GatewayConstraints)


class UITranslationResponse(BaseModel):
    language: str
    strings: dict[str, str]
