@echo off
echo ===================================================
echo   TITAN TRADING SYSTEM v2.0 - INSTITUTIONAL CORE
echo ===================================================
echo.
echo Launching Execution Loop (TrendSurfer Strategy)...
echo.
set PYTHONPATH=%CD%
python -m titan_system.execution.main_loop
pause
