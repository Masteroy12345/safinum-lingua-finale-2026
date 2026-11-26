"""Gestionnaire d'état cross-canal (clé par téléphone normalisé) et journal de diagnostics temps réel."""
from collections import deque
from dataclasses import dataclass, field
import re
from typing import Any


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 9 and digits.startswith("6"):
        return f"237{digits}"
    return digits


@dataclass
class UserSession:
    phone: str
    language: str = "fr"
    pending_tx_id: str | None = None
    pending_tx_trace_id: str | None = None
    pending_op: dict[str, Any] = field(default_factory=dict)
    awaiting_field: str | None = None  # "amount", "beneficiary", "candidate_choice", "language_choice"
    draft_op_type: str | None = None  # "transfer", "airtime", "bill", "fee"
    draft_transfer: dict[str, Any] = field(default_factory=dict)
    candidate_choices: list[dict[str, Any]] = field(default_factory=list)
    last_channel: str = "ussd"


class SessionStore:
    def __init__(self) -> None:
        self._by_phone: dict[str, UserSession] = {}
        self._diagnostics: deque[dict[str, Any]] = deque(maxlen=60)

    def get_or_create(self, phone: str) -> UserSession:
        norm = normalize_phone(phone) or "anonymous"
        if norm not in self._by_phone:
            self._by_phone[norm] = UserSession(phone=norm)
        return self._by_phone[norm]

    def log_diagnostic(self, entry: dict[str, Any]) -> None:
        self._diagnostics.appendleft(entry)

    def get_diagnostics(self) -> list[dict[str, Any]]:
        return list(self._diagnostics)

    def clear_pending(self, session: UserSession) -> None:
        session.pending_tx_id = None
        session.pending_tx_trace_id = None
        session.pending_op = {}
        session.awaiting_field = None
        session.draft_op_type = None
        session.draft_transfer = {}
        session.candidate_choices = []


store = SessionStore()
