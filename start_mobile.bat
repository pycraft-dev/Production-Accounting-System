@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0mobile"

REM Kivy на Windows — только Python 3.8–3.12.

set "READY="
set "VENV_PY="

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; v=sys.version_info[:2]; raise SystemExit(0 if (3, 8) <= v <= (3, 12) else 1)" 2>nul
  if errorlevel 1 (
    echo.
    echo [ВНИМАНИЕ] mobile\.venv собран не на ту версию Python для Kivy.
    echo Удалите папку и запустите снова:
    echo   rmdir /s /q "%CD%\.venv"
    echo.
    pause
    exit /b 1
  )
  set "VENV_PY=%CD%\.venv\Scripts\python.exe"
  set "READY=1"
  goto :run_deps
)

for %%V in (3.12 3.11 3.10 3.9 3.8) do (
  call :try_py_venv %%V
  if defined READY goto :run_deps
)

REM Локальный Python в PATH с нужной версией — создаём venv им
python -c "import sys; v=sys.version_info[:2]; raise SystemExit(0 if (3, 8) <= v <= (3, 12) else 1)" 2>nul
if errorlevel 1 goto :badver

echo Создаю mobile\.venv через "python" из PATH ...
if exist ".venv" rmdir /s /q ".venv"
python -m venv .venv
if errorlevel 1 goto :venv_fail
if not exist ".venv\Scripts\python.exe" goto :venv_fail
set "VENV_PY=%CD%\.venv\Scripts\python.exe"
set "READY=1"
goto :run_deps

:try_py_venv
py -%1 -c "import sys; v=sys.version_info[:2]; raise SystemExit(0 if (3, 8) <= v <= (3, 12) else 1)" 2>nul
if errorlevel 1 goto :eof
echo Создаю mobile\.venv на Python %1 ...
if exist ".venv" rmdir /s /q ".venv"
py -%1 -m venv .venv
if errorlevel 1 (
  echo [пропуск] Python %1: venv не создан ^(часто: нет runtime — см. сообщение py выше^).
  if exist ".venv" rmdir /s /q ".venv"
  goto :eof
)
if not exist ".venv\Scripts\python.exe" (
  echo [пропуск] Python %1: нет .venv\Scripts\python.exe
  if exist ".venv" rmdir /s /q ".venv"
  goto :eof
)
set "VENV_PY=%CD%\.venv\Scripts\python.exe"
set "READY=1"
goto :eof

:venv_fail
echo [ОШИБКА] Не удалось создать .venv. Проверьте права на папку mobile и антивирус.
pause
exit /b 1

:run_deps
if not defined READY goto :badver
if not defined VENV_PY set "VENV_PY=%CD%\.venv\Scripts\python.exe"

echo Установка зависимостей ^(Kivy, KivyMD^)...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Если ошибка про kivy_deps — нужен Python 3.8–3.12 в этом venv:
    "%VENV_PY%" --version
    pause
    exit /b 1
)

if not defined API_BASE_URL set "API_BASE_URL=http://127.0.0.1:8000"

REM set "API_BASE_URL=http://10.0.2.2:8000"
REM set "API_BASE_URL=http://192.168.1.100:8000"

echo.
echo KivyMD-клиент, API=%API_BASE_URL%
echo Для APK на Android см. build_android_apk.bat
echo.
"%VENV_PY%" main.py
if errorlevel 1 pause
exit /b 0

:badver
echo.
echo [ОШИБКА] Для Kivy/KivyMD на Windows нужен Python 3.8–3.12.
echo На 3.13/3.14 нет готовых колёс ^(kivy_deps.sdl2_dev^).
echo.
echo Установите 3.12 и при необходимости привяжите к py launcher:
echo   py install 3.12
echo или полный установщик: https://www.python.org/downloads/
echo Отметьте «Add python.exe to PATH» и «py launcher».
echo.
echo Затем снова запустите start_mobile.bat из корня проекта.
echo.
pause
exit /b 1
