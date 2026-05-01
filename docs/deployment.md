# Развёртывание

## PostgreSQL

Регулярное резервное копирование (пример):

```bash
pg_dump -U pas_user -h localhost production_accounting > backup.sql
```

## Render / Railway

1. Репозиторий с корнем `backend` или задайте root directory.
2. Build: `pip install -r backend/requirements.txt` (или эквивалент).
3. Start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Подключите PostgreSQL (аддон), задайте переменные из `backend/.env.example`.
5. После деплоя: `alembic upgrade head`, при необходимости `python scripts/seed_data.py`.

## Переменные окружения

См. `backend/.env.example`: `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, SMTP, Telegram, `ERP_ADAPTER`, ключ шифрования файлов.
