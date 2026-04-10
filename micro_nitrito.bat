@echo off
cd /d "%~dp0"
start /min cmd /c python -m streamlit run dashboard.py --server.headless true
timeout /t 3 >nul
start http://localhost:3000/micro