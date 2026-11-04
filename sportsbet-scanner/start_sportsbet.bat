@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   MicrobistBets - pornire server + tunel
echo ============================================================

REM 1. Server uvicorn pe :8000 (doar daca nu ruleaza)
curl -s -m 2 -o nul http://127.0.0.1:8000/api/version 2>nul
if errorlevel 1 (
    echo [1/2] Pornesc serverul uvicorn...
    start "MB-server" /min cmd /c "cd /d %~dp0backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 > %~dp0backend_uvicorn.out.log 2>&1"
) else (
    echo [1/2] Serverul ruleaza deja.
)

REM 2. Tunel cloudflared (doar daca nu ruleaza)
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find /I "cloudflared.exe" >nul
if errorlevel 1 (
    echo [2/2] Pornesc tunelul cloudflared...
    start "MB-tunel" /min cmd /c "%~dp0tools\cloudflared.exe tunnel --url http://127.0.0.1:8000 --no-autoupdate > %~dp0tools\cloudflared_out.log 2> %~dp0tools\cloudflared_err.log"
) else (
    echo [2/2] Tunelul ruleaza deja.
)

echo Astept inregistrarea tunelului (~15-30s)...
timeout /t 15 /nobreak >nul

python "%~dp0tools\get_link.py"

echo.
pause
