@echo off
cd /d "%~dp0"
echo Open http://127.0.0.1:8783 in your browser. No API keys or live calls.
py -3 -B changeproof_app/app.py --port 8783
pause
