@echo off
chcp 65001 > nul
cd /d D:\Tele-Daily-Checkin

echo =============================== >> checkin.log
echo Run at %date% %time% >> checkin.log

call .venv\Scripts\activate
set PYTHONIOENCODING=utf-8

python daily_checkin.py >> checkin.log 2>&1

echo Finished at %date% %time% >> checkin.log
echo. >> checkin.log