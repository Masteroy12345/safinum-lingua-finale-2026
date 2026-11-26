"""Client asynchrone pour l'API Bancaire Simulée SAFINUM (propagation stricte de X-Trace-Id et X-Team-Key)."""
from typing import Any
import httpx

from .config import settings


class BankApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str = "",
        candidates: list[dict] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message or code)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.candidates = candidates or []
        self.details = details or {}


class BankClient:
    def __init__(self, timeout_s: float | None = None):
        self.timeout_s = timeout_s or settings.request_timeout_s

    def _headers(self, trace_id: str) -> dict[str, str]:
        return {
            "X-Team-Key": settings.team_key,
            "X-Trace-Id": trace_id,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        trace_id: str,
        base_url: str | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        root = (base_url or settings.bank_api_url).rstrip("/")
        url = f"{root}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            resp = await client.request(
                method=method,
                url=url,
                headers=self._headers(trace_id),
                params=params,
                json=json_body,
            )
        try:
            data = resp.json()
        except Exception:
            data = {"message": resp.text}

        if not isinstance(data, dict):
            data = {"data": data}

        if resp.status_code >= 400:
            raw_err = data.get("error")
            if isinstance(raw_err, dict):
                code = raw_err.get("code") or data.get("code")
                candidates = raw_err.get("candidates") or data.get("candidates") or []
                msg = raw_err.get("message") or data.get("message") or ""
            else:
                # Format officiel API Safinum : {"error": "INSUFFICIENT_FUNDS", "message": "...", ...}
                code = raw_err if isinstance(raw_err, str) and raw_err else data.get("code")
                candidates = data.get("candidates") or []
                msg = data.get("message") or ""
            if not code:
                code = "UNAUTHORIZED" if resp.status_code == 401 else "GENERIC"
            raise BankApiError(resp.status_code, str(code), str(msg), candidates, details=data)

        return data

    async def get_account(self, phone: str, trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        return await self._request("GET", f"accounts/{phone}", trace_id, base_url)

    async def get_transactions(self, phone: str, limit: int, trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        return await self._request("GET", f"accounts/{phone}/transactions", trace_id, base_url, params={"limit": min(limit, 50)})

    async def search_beneficiaries(self, q: str | None, phone: str | None, trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        params = {}
        if q:
            params["q"] = q
        if phone:
            params["phone"] = phone
        return await self._request("GET", "beneficiaries", trace_id, base_url, params=params)

    async def get_fees(self, op_type: str, amount: int, trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        return await self._request("GET", "fees", trace_id, base_url, params={"type": op_type, "amount": amount})

    async def get_billers(self, trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        return await self._request("GET", "billers", trace_id, base_url)

    async def create_transaction(self, payload: dict[str, Any], trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        return await self._request("POST", "transactions", trace_id, base_url, json_body=payload)

    async def update_transaction(self, tx_id: str, payload: dict[str, Any], trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        return await self._request("POST", f"transactions/{tx_id}/update", trace_id, base_url, json_body=payload)

    async def confirm_transaction(self, tx_id: str, trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        return await self._request("POST", f"transactions/{tx_id}/confirm", trace_id, base_url, json_body={})

    async def cancel_transaction(self, tx_id: str, trace_id: str, base_url: str | None = None) -> dict[str, Any]:
        return await self._request("POST", f"transactions/{tx_id}/cancel", trace_id, base_url, json_body={})
