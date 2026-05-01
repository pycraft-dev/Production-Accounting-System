@echo off
chcp 65001 >nul
cd /d "%~dp0mobile"

echo ============================================
echo   Сборка APK (WSL + buildozer)
echo ============================================
echo.
where wsl >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] WSL не найден. Установите WSL2 + Ubuntu, либо добавьте buildozer в PATH и запустите: buildozer android debug
    pause
    exit /b 1
)

echo Запуск: wsl_build_apk.sh ^(venv .buildozer_venv, затем buildozer android debug^)
echo Папка: %CD%
echo.

wsl.exe --cd "%CD%" bash -lc "sed -i 's/\r$//' wsl_build_apk.sh 2>/dev/null; chmod +x wsl_build_apk.sh; ./wsl_build_apk.sh"
set ERR=%ERRORLEVEL%

echo.
if %ERR% equ 0 (
    echo Готово. APK: %CD%\bin\*.apk
    dir /b "%CD%\bin\*.apk" 2>nul
) else (
    echo Сборка завершилась с кодом %ERR%
)
pause
exit /b %ERR%
