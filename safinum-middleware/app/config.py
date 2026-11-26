"""Configuration de Safinum Lingua Middleware (avec chargement automatique de .env)."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

_MW_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _MW_ROOT.parent
# Charger .env local du middleware puis .env racine sans écraser les variables déjà exportées
load_dotenv(_MW_ROOT / ".env", override=False)
load_dotenv(_REPO_ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    team_key: str = os.getenv("SAFINUM_TEAM_KEY", "sbx_votre_cle")
    team_id: str = os.getenv("SAFINUM_TEAM_ID", "Dev space ICT")
    bank_api_url: str = os.getenv("SAFINUM_BANK_API_URL", "https://www.safinum.cm/api/v1").rstrip("/")
    port: int = int(os.getenv("PORT", "3000"))
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    request_timeout_s: float = float(os.getenv("SAFINUM_HTTP_TIMEOUT", "2.0"))
    ui_phonetic_tts: bool = os.getenv("SAFINUM_UI_PHONETIC_TTS", "1") == "1"


settings = Settings()
