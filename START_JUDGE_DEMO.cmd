@echo off
cd /d "%~dp0"
start "" "http://127.0.0.1:8941/judge_demo/"
py -3.12 -B -m http.server 8941 --bind 127.0.0.1
