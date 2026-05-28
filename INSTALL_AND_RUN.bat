@echo off
setlocal
cd /d "%~dp0"

echo Local Business Lead Agent
echo =========================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo First run detected. Installing local environment...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
  if errorlevel 1 (
    echo.
    echo Setup failed. Read the message above.
    pause
    exit /b 1
  )
)

echo Starting app...
call ".venv\Scripts\activate.bat"
streamlit run app.py

pause
