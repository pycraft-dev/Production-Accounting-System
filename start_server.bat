@echo off
chcp 65001 >nul
cd /d "%~dp0backend"

if exist "%~dp0venv\Scripts\activate.bat" call "%~dp0venv\Scripts\activate.bat"
if exist "%~dp0backend\.venv\Scripts\activate.bat" call "%~dp0backend\.venv\Scripts\activate.bat"

echo Запуск API на 0.0.0.0:8000 (остановка: Ctrl+C)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
