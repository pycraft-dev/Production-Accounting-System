# Production Accounting System

Полная инструкция: **[docs/README.md](docs/README.md)**.

## Важно

- Зависимости и код API находятся в **`backend/`**. Команды `pip`, `alembic`, `uvicorn` нужно выполнять **из каталога `backend`** (или задать `PYTHONPATH` на `backend`). Иначе будет `No module named 'app'` и «нет файла requirements.txt».
- **Docker:** ошибка `dockerDesktopLinuxEngine` / `cannot find the file specified` означает, что **Docker Desktop не запущен** (или не установлен). Запустите Docker Desktop и повторите `docker compose`.

## Минимальный старт API (PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Настройте .env (скопируйте из .env.example), поднимите PostgreSQL
python -m alembic upgrade head
python scripts/seed_data.py
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger: http://localhost:8000/docs

## Скрипты в корне репозитория (Windows)

| Файл | Назначение |
|------|------------|
| [launcher.bat](launcher.bat) | **Лаунчер** без чёрного окна (через `pyw` + VBS) |
| [launcher_console.bat](launcher_console.bat) | То же GUI, но с консолью — если лаунчер не появился |
| [start_server.bat](start_server.bat) | API (uvicorn `0.0.0.0:8000`) |
| [start_desktop.bat](start_desktop.bat) | Десктоп (CustomTkinter), переменная `API_BASE_URL` |
| [start_mobile.bat](start_mobile.bat) | Мобильный клиент на ПК (KivyMD), для эмулятора см. комментарии в файле |
| [build_android_apk.bat](build_android_apk.bat) | Подсказка по сборке APK через buildozer (обычно WSL/Linux) |
