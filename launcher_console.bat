@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Лаунчер с окном отладки ^(если GUI не появился — смотрите текст здесь^).
py -3 launcher.py 2>nul
if errorlevel 1 python launcher.py
if errorlevel 1 (
  echo Не удалось запустить launcher.py.
  pause
)
