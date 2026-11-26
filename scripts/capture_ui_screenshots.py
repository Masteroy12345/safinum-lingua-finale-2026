"""Lance temporairement les 3 serveurs FastAPI (3000, 3001, 3002) et capture leurs interfaces web en PNG."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VENV_PY = str(ROOT / ".venv" / "bin" / "python")
CAP_DIR = ROOT / "safinum-middleware" / "docs" / "images" / "captures"
CHROME = shutil.which("google-chrome") or "/home/ravel/bin/google-chrome"


def wait_port(url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.5) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.4)
    raise TimeoutError(f"Timeout en attendant {url}")


def main() -> None:
    CAP_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    procs: list[subprocess.Popen] = []

    try:
        procs.append(subprocess.Popen([VENV_PY, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "3100"], cwd=str(ROOT / "safinum-middleware"), env=env))
        procs.append(subprocess.Popen([VENV_PY, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "3101"], cwd=str(ROOT / "traduction_service_google"), env=env))
        procs.append(subprocess.Popen([VENV_PY, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "3102"], cwd=str(ROOT / "traduction_mot_a_mot"), env=env))

        wait_port("http://127.0.0.1:3100/health")
        wait_port("http://127.0.0.1:3101/health")
        wait_port("http://127.0.0.1:3102/health")

        # Envoyer une requête de démo au middleware pour alimenter le tableau Diagnostics Live
        import httpx
        httpx.post("http://127.0.0.1:3100/middleware", json={
            "trace_id": "live-demo-ussd-01", "channel": "ussd", "phone": "237677000001",
            "language": "dua", "input": {"type": "menu", "text": ""},
        }, timeout=5.0)
        httpx.post("http://127.0.0.1:3100/middleware", json={
            "trace_id": "live-demo-web-02", "channel": "web", "type": "ui_translation",
            "phone": "237677000001", "language": "bbj", "screen": "home",
            "strings": {"nav.home": {"text": "Accueil", "max_chars": 12}, "home.balance_label": {"text": "Solde disponible"}},
        }, timeout=5.0)
        # Pre-chauffer le service Google IA (T5 + CTranslate2) pour un rendu instantane dans Chrome
        httpx.post("http://127.0.0.1:3101/translate", json={
            "text": "bonjor je veu envoye 5 000 FCFA a 677000001 sil vou plait",
            "target_language": "ewo",
            "auto_correct": True,
        }, timeout=30.0)

        targets = [
            ("http://127.0.0.1:3100/", CAP_DIR / "ui_middleware_3000.png"),
            ("http://127.0.0.1:3100/studio", CAP_DIR / "ui_studio_3000.png"),
            ("http://127.0.0.1:3101/", CAP_DIR / "ui_google_3001.png"),
            ("http://127.0.0.1:3102/", CAP_DIR / "ui_mot_a_mot_3002.png"),
        ]
        for url, out_png in targets:
            subprocess.run(
                [
                    CHROME,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--window-size=1360,920",
                    "--virtual-time-budget=12000",
                    f"--screenshot={out_png}",
                    url,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("Capture generee :", out_png)
    finally:
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()


if __name__ == "__main__":
    main()
