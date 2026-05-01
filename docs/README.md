# Production Accounting System
Монорепозиторий: backend (FastAPI), desktop (CustomTkinter), mobile (KivyMD).

## Лаунчер (Windows)

**launcher.bat** в корне — окно с кнопками (без чёрной консоли: `pyw` + `launcher_start.vbs`). Если окно не открылось — **[launcher_console.bat](launcher_console.bat)** для отладки.

**Все команды для API выполняйте из каталога `backend`.** В корне репозитория нет `requirements.txt` и пакет `app` не на пути Python — оттуда `pip install`, `alembic`, `uvicorn app.main:app` дадут ошибки.

## Быстрый старт (backend)

1. Установите PostgreSQL 15+ и создайте БД `production_accounting`.
2. Скопируйте `backend/.env.example` в `backend/.env`, задайте `DATABASE_URL`, `JWT_SECRET_KEY`, при необходимости `FILES_ENCRYPTION_KEY_BASE64`.
3. Перейдите в **`backend`** и выполните:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
python scripts\seed_data.py
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Без PostgreSQL (файл SQLite):** в `backend/.env` задайте одну строку  
`DATABASE_URL=sqlite+pysqlite:///./dev.db`  
(и закомментируйте/удалите URL с `postgresql`). После этого снова `alembic upgrade head` и `seed` — пароль `pas_user` не нужен.

Linux/macOS: `source .venv/bin/activate`, путь к seed: `python scripts/seed_data.py`.

### Частые ошибки

**`password authentication failed for user "pas_user"`** — либо создайте пользователя и БД в PostgreSQL:

```sql
CREATE USER pas_user WITH PASSWORD 'pas_secret';
CREATE DATABASE production_accounting OWNER pas_user;
```

либо переключитесь на **SQLite**: `DATABASE_URL=sqlite+pysqlite:///./dev.db` в `backend/.env`, затем снова `alembic upgrade head` и `seed`.

**`No module named 'app'` при `python scripts\seed_data.py`** — скрипт должен запускаться из каталога **`backend`** (обновите файл `scripts/seed_data.py` до последней версии — в нём добавляется корень backend в `sys.path`).

Документация OpenAPI: http://localhost:8000/docs

### Docker

**Если видите ошибку про `dockerDesktopLinuxEngine` или `pipe`:** запустите **Docker Desktop** и дождитесь статуса «running», затем повторите команду.

Из корня репозитория:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Затем в контейнере API выполните миграции и seed (один раз):

```bash
docker compose -f docker/docker-compose.yml exec api python -m alembic upgrade head
docker compose -f docker/docker-compose.yml exec api python scripts/seed_data.py
```

## Клиенты

- **Desktop:** `cd desktop`, `pip install -r requirements.txt`, `set API_BASE_URL=http://localhost:8000`, `python main.py`
- **Mobile (отладка на ПК):** из корня репозитория запустите **`start_mobile.bat`** (он проверит версию Python и выполнит `pip install`). На **Windows для Kivy нужен Python 3.8–3.12**; на 3.13/3.14 колёса `kivy_deps.sdl2_dev` недоступны — поставьте [Python 3.12](https://www.python.org/downloads/), затем `py -3.12 -m venv mobile\.venv` и установите зависимости в этом venv. Для Android — `buildozer`, см. `mobile/buildozer.spec`.

## Учётные записи после seed

- **`admin`** / **`admin`** (демо после `seed_data`). После первого входа приложение запросит **смену пароля** (не короче 8 символов).
- **`worker1`** / **`worker12345`**
- **`constructor1`** / **`constructor12345`**

## Тесты

```bash
cd backend
pytest
```

## Доп. документация

- [Локальный хостинг на ПК](DEPLOY_LOCAL.md)
- [Автообновление клиентов](AUTO_UPDATE.md)
- [Сеть (LAN, ngrok, облако)](NETWORK_SETUP.md)
- [Руководство администратора](ADMIN_GUIDE.md)
- [Руководство пользователя](USER_GUIDE.md)
