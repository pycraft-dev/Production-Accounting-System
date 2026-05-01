# Интеграция с 1С / ERP

В версии 1 реализован **адаптер**:

- `ERP_ADAPTER=mock` — без сети, фиктивный каталог.
- `ERP_ADAPTER=onec_http` — HTTP-клиент к вашему REST/OData/HTTP-сервису.

Переменные: `ERP_BASE_URL`, `ERP_API_TOKEN`, `ERP_TIMEOUT_SECONDS`.

## Ожидаемые конечные точки (пример для `onec_http`)

- `GET {base}/catalog` — JSON-массив или объект с полем `items`; элементы с полем `external_id`.
- `POST {base}/events` — приём пакета событий из поля `items` экспорта.

Под конкретную конфигурацию 1С пути и формат тела нужно согласовать; маппинг справочников сохраняется в таблице `erp_entity_links`.

## Админ-API

- `POST /api/erp/import` — импорт каталога.
- `POST /api/erp/export` — JSON `{"items": [...]}`.
- `GET /api/erp/status` — последние записи синхронизации.
