@echo off
echo ===================================================
echo   SAFINUM LINGUA - Demarrage du Middleware Final
echo ===================================================

if not exist .venv (
    echo [1/3] Creation de l'environnement virtuel Python...
    py -m venv .venv
)

call .venv\Scripts\activate.bat
echo [2/3] Installation des dependances...
pip install -q -r requirements.txt

echo [3/3] Lancement du serveur sur http://localhost:3000 ...
echo Dashboard Diagnostics : http://localhost:3000/
echo Endpoint Gateway      : http://localhost:3000/middleware
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
