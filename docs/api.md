# API (кратко)

Базовый префикс: `/api`.

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/login` | Вход: JSON ``login`` или ``email`` + ``password``. Например **admin** / **admin** или **worker1** |
| POST | `/auth/refresh` | Обновление пары токенов |
| POST | `/auth/register` | 403 |
| POST | `/auth/change-password` | Смена пароля (Bearer): ``current_password``, ``new_password`` (≥8) |
| GET | `/version` | Версии API и клиентов, URL пакетов обновления |
| GET | `/updates/desktop/latest` | Скачивание zip (если задано в манифесте) |
| GET | `/updates/mobile/latest` | Скачивание APK (если задано в манифесте) |
| GET | `/admin/docs` | Список файлов `*.md` из каталога `docs/` (admin) |
| GET | `/admin/docs/{filename}` | Текст одного файла (только `.md`, admin) |
| GET/POST | `/admin/users` | Пользователи (admin) |
| PATCH | `/admin/users/{id}` | Редактирование (admin) |
| POST | `/admin/users/{id}/change-password` | Смена пароля пользователя (admin) |
| DELETE | `/admin/users/{id}` | Отключение учётной записи (мягкое удаление, admin) |
| GET | `/defects/workshops` | Список цехов для формы брака (Барнаул, Павловск) |
| GET | `/files/{id}` | Скачать вложение (Bearer); открыть в просмотрщике ОС |
| GET/CRUD | `/defects` | Брак; список: ``mine=true`` — только заявки текущего пользователя |
| POST | `/defects/{id}/photos` | Вложение фото или видео (до 50 МБ) |
| * | `/schematics/...` | Версии схем |
| * | `/daily-reports` | Ежедневные отчёты |
| * | `/equipment` | Оборудование и простои |
| POST | `/analytics/oee` | OEE за период |
| GET | `/export/defects?fmt=xlsx|pdf` | Экспорт |
| POST | `/erp/import`, `/erp/export` | ERP (admin) |

Полная схема: `/docs` у сервера.
