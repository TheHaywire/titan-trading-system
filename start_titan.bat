@echo off
title Titan Launcher
echo ====================================================
echo      TITAN QUANT SYSTEM - PROFESSIONAL EDITION
echo ====================================================
echo.
echo [1/3] Initializing Environment...
echo.

echo [2/3] Starting Mission Control (Dashboard)...
start "Titan Monitor" python titan_system/dashboard/monitor.py

echo [3/3] Starting Watchdog (Engine Manager)...
echo (Output will appear here)
python titan_system/watchdog.py

echo.
echo ✅ System is Online.
echo    - Watchdog window manages the Engine (Close it to stop trading)
echo    - Monitor window shows Real-time Analysis
echo.
pause
