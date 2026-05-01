@echo off
chcp 65001 >nul
cd /d "%~dp0desktop"

REM Виртуальное окружение в корне репозитория (если есть)
if exist "%~dp0venv\Scripts\activate.bat" call "%~dp0venv\Scripts\activate.bat"
if not defined API_BASE_URL set "API_BASE_URL=http://127.0.0.1:8000"

echo Десктоп-клиент, API=%API_BASE_URL%
echo Перед запуском поднимите сервер: start_server.bat
echo.
python main.py
if errorlevel 1 pause
