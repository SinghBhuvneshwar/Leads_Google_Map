@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found. Run setup_windows.ps1 first.
  exit /b 1
)

call ".venv\Scripts\activate.bat"
streamlit run app.py
