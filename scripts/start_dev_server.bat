@echo off
chcp 65001 >nul
echo ==========================================
echo   BESEDKA - ZAPUSK SERVERA RAZRABOTKI
echo ==========================================
echo.

echo Proveryaem tekushchie processy...
netstat -ano | findstr ":800" >nul 2>&1
if %errorlevel% equ 0 (
    echo VNIMANIE: Naydeny zapushchennye servery na portakh 800x
    echo.
)

echo Ostanavlivaem starye processy...
taskkill /IM "python.exe" /F >nul 2>&1
taskkill /IM "daphne.exe" /F >nul 2>&1
echo Processy ostanovleny

echo.
echo Proveryaem nastroyki Channel Layers...
python -c "from django.conf import settings; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local'); import django; django.setup(); print('Django nastroyen pravilno')" 2>nul
if %errorlevel% neq 0 (
    echo OSHIBKA konfiguratsii Django
    pause
    exit /b 1
)

echo.
echo Zapuskaem ASGI server na portu 8001...
echo URL: http://127.0.0.1:8001/
echo Chat: http://127.0.0.1:8001/chat/general/
echo Adminka: http://127.0.0.1:8001/admin/
echo.
echo Zapusk mozhet zanyat neskolko sekund...
echo.

daphne -b 127.0.0.1 -p 8001 config.asgi:application

echo.
echo Server ostanovlen. Nazmite lyubuyu klavishu dlya vykhoda...
pause >nul
