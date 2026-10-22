@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 python -B design_server.py --design a --port 8940 --open-browser
) else (
 py -3 -B design_server.py --design a --port 8940 --open-browser
)
pause
