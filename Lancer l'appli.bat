@echo off
setlocal
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\nodejs;%PATH%"
cd /d "%~dp0"

rem L'appli est passée de Streamlit à une PWA React + API FastAPI : il faut
rem lancer les deux serveurs (backend port 8000, frontend port 5173) puis
rem ouvrir le navigateur sur le frontend -- Streamlit (app.py) n'est plus le
rem point d'entrée.
start "Simulafoot API" cmd /k "cd /d "%~dp0" && uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
start "Simulafoot UI" cmd /k "cd /d "%~dp0ui" && npm run dev"

timeout /t 4 /nobreak >nul
start "" "http://localhost:5173"
