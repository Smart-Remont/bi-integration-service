# AGENTS.md — integrations-sr

Инструкция для ИИ-агентов и разработчиков. Читайте перед изменениями в репозитории.

## Назначение проекта

FastAPI-сервис — тонкий HTTP-слой над PostgreSQL stored functions (`asyncpg`, без ORM).

## Два типа API

| Тип | Префикс | Пример | Шаблон |
|-----|---------|--------|--------|
| Внутренний REST API | `/api/v1/...` | `GET /api/v1/ddu_contractors` | `features/ddu_contractor/` |
| BIG Integration | `/api/big_integration/...` | `POST /api/big_integration/request-event-v3` | `features/big_integration/<endpoint>/` |

Не смешивать паттерны между типами.

---

## BIG Integration

API интеграции ДДУ (BIG). Документация: **[docs/big-integration.md](docs/big-integration.md)**.

Basic Auth, JSON-тело без Pydantic (валидация в SP), ответ в envelope `data/response/error`.

### Структура

```text
features/big_integration/
├── auth.py              # HTTP Basic (INTEGRATION_HS_BI_*)
├── db.py                # scalar_from_sp_rows()
├── errors.py            # BigIntegrationDatabaseError, текст из PostgreSQL {…}
├── http.py              # read_json_object() — парсинг тела
├── responses.py         # envelope {"data","response","error"}
├── router.py            # агрегатор под-роутеров
└── <endpoint_name>/
    ├── deps.py
    ├── repo.py
    ├── router.py
    └── service.py
```

Подключение в `app/src/routers/big_integration.py` + `api_prefix_config.big_integration` в `routers/config.py`.

### URL

```text
/api + /big_integration + /<route>
```

Пример: `POST /api/big_integration/request-event-v3`.

**Эндпоинты** (auth `INTEGRATION_HS_BI_*`):

| Route | Method | БД |
|-------|--------|-----|
| `request-create-v3` | POST | `ddu__create_request_v2` → `ddu__request_get` |
| `request-event-v3` | POST | `ddu__request_event_v3` → `ddu__request_get` |
| `repair-pack-prices` | POST | `ddu_repair_pack_info__get` |
| `ddu-flat-info-multiple` | POST | `ddu_flat_info_multiple` |
| `ddu-resident-agreement-status` | POST | `ddu_resident_agreement__log_insert` |
| `request-info` | GET | `ddu_request_info` |
| `request-status-info` | GET | `ddu_request_and_status_info` |
| `ddu-request-info` | GET | `ddu_request_info_by_client_request` |
| `ddu-flat-info` | GET | `ddu_flat_info` |
| `request-constructives` | POST | `ddu_client_material__read`, `ddu_client_filling__read`, `ddu_request_full_info` |
| `remont-preset-list-v2` | POST | `ddu__preset_list_v2`, `render_*` |
| `remont-preset` | POST | `ddu__preset_list_v2`, `render_filling__*` |
| `big-notify-client` | POST | `big_notify_client` |
| `request-create` | POST | `ddu__create_request` → `ddu__request_get` (legacy v1, `deprecated=True`) |
| `request-create-v2` | POST | `ddu__create_request_v2` → `ddu__request_get`, без `client_request_id` (legacy v2, `deprecated=True`) |
| `request-event` | POST | `ddu__request_event` → `ddu__request_get`, без `client_request_id` (legacy v1, `deprecated=True`) |
| `remont-preset-list` | POST | `ddu__preset_list` (legacy v1, `deprecated=True`) |

Остальной `IntegrationController` — отдельные модули `features/*` (export ✅, BI ✅, SMS, payments, signing, leads). См. `agent-memory/big-integration-cutover/README.md`.

---

## DDU Export API

Отдельный от BIG Integration домен — своя Basic Auth (`DDU_EXPORT_AUTH_*`), свой роутер, свой
модуль ошибок/envelope. Документация: **[docs/ddu-export.md](docs/ddu-export.md)**.

### Структура

```text
features/ddu_export/
├── auth.py       # HTTP Basic (DDU_EXPORT_AUTH_*), отдельные credentials от hs_bi
├── constants.py  # DDU_EXPORT_MODULE_CODE
├── errors.py     # DduExportDatabaseError (использует src/pg_error_utils.py)
├── responses.py  # envelope {"data","response","error"} — своя копия, без импорта из big_integration
├── router.py     # агрегатор под-роутеров
└── <endpoint_name>/
    ├── deps.py
    ├── repo.py
    ├── router.py
    └── service.py
```

### URL

```text
/api + /ddu_export + /<route>
```

**Эндпоинты** (auth `DDU_EXPORT_AUTH_*`):

| Route | Method | БД |
|-------|--------|-----|
| `ddu-flat-remont-info` | GET | `ddu_flat_remont_info` (группировка по комнатам в service) |
| `ddu-resident-list` | GET | `ddu_resident_list` |
| `ddu-flat-list-by-resident` | GET | `ddu_flat_list_by_resident` |
| `ddu-room-list` | GET | `ddu_room_list` |
| `ddu-room-type-list` | GET | `ddu_room_type_list` |

**Не перенесено:** `export-table-read` (SP `rest.export_table_read` не существует в БД + security risk generic-дампа таблиц), `sms-notify-status` (не ДДУ-домен, см. этап 6 SMS/Kcell).

---

## Legacy BI/CRM API

BI-группа `IntegrationController` — рендер/наличие, отчёты, лиды BI-приложения/CRM. Та же
Basic Auth-учётка, что у BIG Integration (`hs_bi`), но **другой конверт ответа**
(`error.code`, HTTP 400 при ошибке, `data` = код `P0xx`). Документация:
**[docs/legacy-bi.md](docs/legacy-bi.md)**.

### Структура

```text
features/legacy_bi/
├── auth.py             # реэкспорт BigIntegrationBasicAuthDep — та же учётка
├── constants.py         # LEGACY_BI_MODULE_CODE
├── errors.py             # LegacyBiDatabaseError + legacy_bi_error_code() (P0xx)
├── responses.py         # envelope {"data","response","error":{"code","message"}}
├── json_helpers.py     # parse_scalar_json — SP возвращают JSON-строку, не jsonb
├── router.py             # агрегатор под-роутеров
└── <endpoint_name>/
    ├── deps.py
    ├── repo.py
    ├── router.py
    └── service.py
```

### URL

```text
/api + /legacy_bi + /<route>
```

**Эндпоинты** (auth `INTEGRATION_HS_BI_*`): `sr-render`, `sr-request-list`, `sr-preset-list`,
`sr-render-avail`, `sr-stage`, `sr-showroom-report`, `sr-resident-report`, `sr-remont-avail`,
`remont-avail`, `get-constructives`, `change-request-status`, `bigapp-form`, `big-crm-form` —
детали и тела запросов в [docs/legacy-bi.md](docs/legacy-bi.md).

**Не перенесено** (SP не существует в БД или сигнатура разошлась с PHP-моделью):
`crm-create-client-request-empty`, `crm-create-client-request-agreement`, `create-request`,
`sr-remont-report`.

### HTTP-контракт

**Auth:** `Authorization: Basic`, пользователь/пароль из `INTEGRATION_HS_BI_USER`, `INTEGRATION_HS_BI_PASSWORD` (`app/src/config.py`).

**Запрос:** `Content-Type: application/json`, тело передаётся в SP **без Pydantic-валидации** (все проверки в БД).

**Успех (200):** envelope, где `data` — **первая строка refcursor** как JSON-объект (ключи и `null` как вернул PostgreSQL):

```json
{
  "data": {
    "client_request_id": 2916069,
    "application_id": null,
    "order_id": "318796",
    "deal_id": null
  },
  "response": true,
  "error": { "message": "" }
}
```

**Ошибка (500):**

```json
{
  "data": null,
  "response": false,
  "error": { "message": "Поле \"client_request_id\" не заполнено [ДДУ]" }
}
```

Текст `message` — из `raise exception '{…}'` в SP; фигурные скобки снимаются в `clean_postgres_error_message()`.

Невалидный JSON до БД:

```json
{
  "data": null,
  "response": false,
  "error": { "message": "Invalid JSON" }
}
```

### Поток (на примере request-event-v3)

```text
router  → read_json_object(Request)
service → repo.ddu_request_event_v3(body)  → repo.ddu_request_get(id)
repo    → call_sp("rest.ddu__request_event_v3", json.dumps(body), module_code="DDU")
repo    → call_sp("rest.ddu__request_get", id, cursor=True, module_code="DDU")
```

Ответ success — envelope с `data = rows[0]` после `cursor=True`, без Pydantic.

### БД: правила `call_sp`

1. **JSON-аргумент:** передавать `json.dumps(payload)`, не `dict` с `$1::jsonb` вручную — иначе asyncpg может ожидать `str`.
2. **Скаляр из функции:** `scalar_from_sp_rows(rows)` из `big_integration/db.py`.
3. **Refcursor:** `cursor=True` — `call_sp` подставит `@cur_*` первым аргументом (см. `BaseRepository`).
4. **Ошибки `call_sp`:** ловить `Exception`, преобразовывать через `to_big_integration_database_error()` — иначе `map_asyncpg_errors` даст `InfrastructureError` без текста SP.
5. **`module_code`:** для DDU-интеграций использовать `"DDU"`.

### Добавить новый big integration endpoint

1. Создать `features/big_integration/<name>/` (`router`, `deps`, `service`, `repo`).
2. В `repo.py` — только `call_sp`, без сырого `connection.fetchval` / `execute`.
3. В `router.py`:

```python
@router.post("/my-route")
async def my_route(request: Request, _: BigIntegrationBasicAuthDep, service: MyServiceDep) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.handle(body)
```

4. В `service.py` — оркестрация SP, `big_integration_success_response(row)`, `big_integration_error_response(exc.message)` при `BigIntegrationDatabaseError`.
5. Подключить роутер в `features/big_integration/router.py`.

### Чего не делать в big integration

- Использовать legacy envelope `data` / `response` / `error` для всех big integration эндпоинтов.
- Не валидировать обязательные поля в Pydantic — только SP.
- Не использовать `BaseSchema` / camelCase для тел запроса и ответа.
- Не ходить в БД из `router.py`.
- Не выполнять мутирующий SQL без явного запроса пользователя.

---

## Внутренний API (`/api/v1`)

См. `features/ddu_contractor/`:

- Pydantic `BaseSchema` для ответов;
- префиксы в `routers/config.py`, подключение в `routers/v1.py`;
- ошибки БД → глобальные handlers в `exceptions/handler.py` (`{"detail": "..."}`).

---

## File Storage (`/api/v1/storage`)

Async-загрузка файлов **только в MinIO** (без office proxy и локального диска).

### Env

| Переменная | Назначение |
|------------|------------|
| `STORAGE_PUBLIC_URL` | База для публичного URL (`+ /documents/...`). Пустое → `OFFICE_PUBLIC_URL` |
| `MINIO_ENDPOINT` | S3 API, напр. `https://s3.smartremont.kz` |
| `MINIO_BUCKET` | Бакет, напр. `smartremont` |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | Ключи приложения |
| `MINIO_REGION` | `us-east-1` |
| `STORAGE_API_USER` / `STORAGE_API_PASSWORD` | Basic Auth API (fallback → installment) |

### HTTP

```text
GET  /api/v1/storage/config   — MinIO config без секретов
GET  /api/v1/storage/modes    — enum mode + описания
POST /api/v1/storage/upload   — multipart: file + mode (form)
```

**Auth:** Basic (`STORAGE_API_*`).

**Ошибки upload:**
- `400` — пустой файл или неизвестный `mode`
- `503` — MinIO не сконфигурирован
- `502` — ошибка PUT в MinIO

**Ответ upload (201):**

```json
{
  "filename": "photo.jpg",
  "path": "/documents/2026.09.07/material_photo/material_photo_orig_....jpg",
  "ext": "jpg",
  "fileUrl": "https://office.smartremont.kz/documents/..."
}
```

Код: `app/src/features/storage/`, lib `app/src/storage/file_store.py`.

Документация: `/scalar`, `/docs`.

---

## Общие правила

- Импорты: `from src....`
- Локальный запуск команд из `app/`: `cd app && uvicorn src.main:app --reload`
- Не коммитить `app/.env`
- Не писать в БД (INSERT/UPDATE/migrations) без явного подтверждения
- Минимальный diff, без лишних абстракций
- Подробный onboarding: [README.md](README.md)
