# AGENTS.md — integrations-sr

Инструкция для ИИ-агентов и разработчиков. Читайте перед изменениями в репозитории.

## Назначение проекта

FastAPI-сервис — тонкий HTTP-слой над PostgreSQL stored functions (`asyncpg`, без ORM).

## Два типа API

| Тип | Префикс | Пример | Шаблон |
|-----|---------|--------|--------|
| Внутренний REST API | `/api/v1/...` | `GET /api/v1/ddu_contractors` | `features/ddu_contractor/` |
| Legacy big integration | `/api/big_integration/...` | `POST /api/big_integration/request-event-v3` | `features/big_integration/<endpoint>/` |

Не смешивать паттерны между типами.

---

## Big integration (legacy-замена Zend)

Используется для эндпоинтов, которые раньше жили в PHP (`IntegrationController`): Basic Auth, сырой JSON в SP, ответ в legacy envelope `data/response/error`.

### Структура

```text
features/big_integration/
├── auth.py              # HTTP Basic (INTEGRATION_HS_BI_*)
├── db.py                # scalar_from_sp_rows()
├── errors.py            # BigIntegrationDatabaseError, текст из PostgreSQL {…}
├── http.py              # read_json_object() — парсинг тела
├── responses.py         # legacy envelope: {"data","response","error"}
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

### HTTP-контракт

**Auth:** `Authorization: Basic`, пользователь/пароль из `INTEGRATION_HS_BI_USER`, `INTEGRATION_HS_BI_PASSWORD` (`app/src/config.py`).

**Запрос:** `Content-Type: application/json`, тело передаётся в SP **без Pydantic-валидации** (все проверки в БД).

**Успех (200):** тело = legacy envelope, где `data` — **первая строка refcursor** как JSON-объект (ключи и `null` как вернул PostgreSQL):

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

## Общие правила

- Импорты: `from src....`
- Локальный запуск команд из `app/`: `cd app && uvicorn src.main:app --reload`
- Не коммитить `app/.env`
- Не писать в БД (INSERT/UPDATE/migrations) без явного подтверждения
- Минимальный diff, без лишних абстракций
- Подробный onboarding: [README.md](README.md)
