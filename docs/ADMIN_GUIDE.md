# Руководство администратора

## Первый вход

- Учётная запись по умолчанию после `scripts/create_first_admin.py` или `seed_data.py`: логин **`admin`**, пароль **`admin`**.
- Признак **`must_change_password`**: после входа клиент потребует сменить пароль на более длинный (не короче 8 символов).

## Пользователи

- Регистрация через API отключена (**403** на `/auth/register`).
- Создание и правки — только из приложений с ролью **admin** или через `POST/PATCH` админ‑API (Swagger `/docs`).
- **Удаление** в API реализовано как **отключение** (`is_active=false`), чтобы не нарушать связанные записи (брак и др.).
- Смена пароля пользователя: `POST /api/admin/users/{id}/change-password` с телом `{"new_password": "..."}`.

## Аудит

- Входы фиксируются действием **`auth.login`** в `/api/admin/audit`.
- Создание/изменение пользователей — `user.create`, `user.update`, `user.change_password`, `user.deactivate`.

## Обновления клиентов

См. **`docs/AUTO_UPDATE.md`**: манифест в каталоге `updates/`, версии в `desktop/version.json` и `mobile/version.json`.

## Развёртывание на ПК

См. **`docs/DEPLOY_LOCAL.md`**.
