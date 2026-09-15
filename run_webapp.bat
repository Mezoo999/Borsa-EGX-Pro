@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   EGX Pro — بوابة الويب (FastAPI + JS)
echo   http://localhost:8000
echo ========================================
echo   للإيقاف: Ctrl + C
echo ========================================
set PYTHONIOENCODING=utf-8
start "" http://localhost:8000
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 -m uvicorn webapp.server:app --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn webapp.server:app --host 127.0.0.1 --port 8000
)
pause
