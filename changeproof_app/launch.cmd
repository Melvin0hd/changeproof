@echo off
setlocal
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 -B "%~dp0launch.py" %*
) else (
  python -B "%~dp0launch.py" %*
)
if errorlevel 1 pause
