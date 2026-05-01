@echo off
cd /d %~dp0
set PYTHONPATH=%CD%
pyinstaller --noconfirm --clean app.spec
