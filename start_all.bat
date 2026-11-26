@echo off
cd /d "%~dp0"
echo Demarrage des 3 services SAFINUM Lingua...
start "Safinum Middleware (3000)" cmd /k "cd /d %~dp0safinum-middleware && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 3000"
start "Safinum Service Google IA (3001)" cmd /k "cd /d %~dp0traduction_service_google && ..\.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 3001"
start "Safinum Mot-a-Mot (3002)" cmd /k "cd /d %~dp0traduction_mot_a_mot && ..\.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 3002"
echo Tous les serveurs sont lances : ports 3000, 3001, 3002.
