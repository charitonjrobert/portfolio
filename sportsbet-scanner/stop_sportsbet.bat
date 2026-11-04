@echo off
REM Opreste MicrobistBets: omoara tunelul + procesul care asculta pe :8000.
taskkill /F /IM cloudflared.exe >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%P >nul 2>&1
echo MicrobistBets oprit (server + tunel).
pause
