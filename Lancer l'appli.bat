@echo off
setlocal
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
cd /d "%~dp0"
uv run streamlit run app.py --server.showEmailPrompt=false
pause
