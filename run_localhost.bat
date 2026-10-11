@echo off
title AuthGuard Localhost Server
echo ========================================================
echo  Starting AuthGuard Flask Server on Localhost...
echo ========================================================
cd /d "%~dp0"

echo Opening browser...
start http://127.0.0.1:5000

echo Starting Python Flask App...
py app.py

pause
