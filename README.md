# integrations-sr

FastAPI-сервис интеграций для Smart Remont. Проект построен как тонкий API-слой над PostgreSQL: HTTP-запросы проходят через FastAPI-роутеры, сервисы и репозитории, а данные читаются из БД через `asyncpg` и PostgreSQL stored functions.

Этот README также служит инструкцией для ИИ-агентов вроде Cursor: где что лежит, какие паттерны уже приняты и как добавлять новый код без ломки архитектуры.

## Стек

- Python `>=3.14`
- FastAPI, Starlette, Uvicorn, Gunicorn
- PostgreSQL через `asyncpg`
- Pydantic v2 для схем
- `pyhumps` для camelCase JSON-алиасов
- `python-dotenv` для локального `.env`
- `uv` для зависимостей
- Docker / Docker Compose

## Быстрый старт

Установить зависимости:

```bash
uv sync
```

Создать локальный env-файл:

```bash
cp app/.env.example app/.env
```

Заполнить переменные:

```env
POSTGRES_PASSWORD=
POSTGRES_USER=
POSTGRES_DB=
POSTGRES_HOST=
POSTGRES_PORT=

DB_POOL_MIN_SIZE=10
DB_POOL_MAX_SIZE=50
```

Запустить локально из директории `app`, потому что импорты в проекте используют корень `src`:

```bash
cd app
./run
```

Альтернативный dev-запуск:

```bash
cd app
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Запуск через Docker:

```bash
docker compose up --build
```

В Docker Compose порт хоста `80` прокинут на порт приложения `8000`.

## Основные entrypoints

- `app/src/main.py` - создание FastAPI-приложения, lifecycle, CORS, exception handlers, подключение главного роутера.
- `app/run_main.py` - запуск Gunicorn-приложения.
- `app/run` - исполняемый Python-скрипт, используемый как Docker `CMD`.
- `app/_gunicorn/` - настройки Gunicorn.
- `docker-compose.yaml` - запуск backend-сервиса и watch-настройки для Docker Compose.

## Поток запроса

```text
HTTP
  -> FastAPI app: app/src/main.py
  -> main router: app/src/routers/
  -> feature router: app/src/features/<feature>/router.py
  -> service: app/src/features/<feature>/service.py
  -> repository: app/src/features/<feature>/repo.py
  -> PostgreSQL stored function через BaseRepository.call_sp()
```

Текущий пример feature-модуля: `app/src/features/ddu_contractor/`.

## Структура проекта

```text
.
├── README.md
├── Dockerfile
├── docker-compose.yaml
├── pyproject.toml
├── uv.lock
└── app
    ├── .env.example
    ├── run
    ├── run_main.py
    ├── prestart.sh
    ├── _gunicorn/
    └── src/
        ├── main.py
        ├── config.py
        ├── database/
        ├── exceptions/
        ├── features/
        ├── repository/
        ├── routers/
        ├── schema/
        └── service/
```

### Ответственность директорий

- `app/src/features/` - главная точка расширения. Каждый бизнес-модуль оформляется отдельной вертикальной feature-директорией.
- `app/src/routers/` - агрегация API-роутеров и общие API-префиксы.
- `app/src/database/` - конфиг БД, глобальный connection pool и FastAPI dependency для подключения.
- `app/src/repository/` - базовый репозиторий и низкоуровневый доступ к БД.
- `app/src/service/` - базовый сервисный слой.
- `app/src/schema/` - базовая Pydantic-схема.
- `app/src/exceptions/` - инфраструктурные и доменные исключения, маппинг ошибок БД в HTTP-ответы.
- `app/_gunicorn/` - production-style запуск через Gunicorn.

## Архитектурные паттерны

### 1. Вертикальные feature-модули

Новые бизнес-возможности добавляются в `app/src/features/<feature_name>/`.

Рекомендуемая структура feature:

```text
features/<feature_name>/
├── deps.py
├── repo.py
├── router.py
├── schemas.py
└── service.py
```

Назначение файлов:

- `schemas.py` - Pydantic-модели запроса/ответа. Наследовать от `BaseSchema`.
- `repo.py` - класс `<Feature>Repository(BaseRepository)`. Только доступ к БД.
- `service.py` - класс `<Feature>Service(BaseService)`. Бизнес-логика и оркестрация репозиториев.
- `deps.py` - FastAPI dependency chain: `Connection -> Repository -> Service`.
- `router.py` - HTTP endpoint-ы, `APIRouter`, параметры запроса и вызов сервиса.

Текущий эталонный пример - `ddu_contractor`.

### 2. Router -> Service -> Repository

Роутер не должен напрямую ходить в БД. Репозиторий не должен знать про HTTP.

Правильное разделение:

- `router.py` принимает HTTP-параметры и вызывает метод сервиса.
- `service.py` содержит бизнес-решение и вызывает один или несколько репозиториев.
- `repo.py` вызывает stored functions или, если необходимо, низкоуровневые `fetch`, `fetchrow`, `execute`.

### 3. Dependency Injection

Feature-зависимости оформляются в `deps.py` через `Annotated` и `Depends`.

Пример паттерна:

```python
def get_example_service(
    connection: DatabaseConnectionDep,
) -> ExampleService:
    repository = ExampleRepository(connection=connection)
    return ExampleService(example_repository=repository)


ExampleServiceDep = Annotated[
    ExampleService,
    Depends(get_example_service),
]
```

В роутере сервис инжектится через alias:

```python
@router.get("/")
async def list_examples(example_service: ExampleServiceDep):
    return await example_service.list_examples()
```

### 4. База данных через connection pool

Pool создается на старте приложения в `app/src/main.py` через `init_db_pool()` и закрывается при shutdown через `close_db_pool()`.

На каждый request dependency `DatabaseConnectionDep` выдает `asyncpg.Connection` внутри транзакции:

```python
async with db_pool.acquire() as connection:
    async with connection.transaction():
        yield connection
```

Это значит:

- успешный request коммитит транзакцию;
- exception откатывает транзакцию;
- долгие операции внутри endpoint-а держат транзакцию открытой.

### 5. Stored functions вместо ORM

В проекте нет ORM. Основной способ доступа к данным - PostgreSQL stored functions через `BaseRepository.call_sp()`.

Пример:

```python
rows = await self.call_sp("public.list_ddu_contractor", cursor=True)
return [DduContractor.model_validate(row) for row in rows]
```

`call_sp()`:

- валидирует имя функции;
- умеет работать с refcursor через `cursor=True` или аргументы вида `"@cur"`;
- выставляет session context `myapp.user_id` и `myapp.module_code`;
- маппит ошибки `asyncpg` в инфраструктурные исключения.

Если нужна user-scoped логика в БД, передавайте `session_user_id`:

```python
await self.call_sp(
    "public.some_function",
    some_arg,
    cursor=True,
    session_user_id=user_id,
    module_code="MYSPACE",
)
```

### 6. Схемы и JSON casing

Все API-схемы должны наследоваться от `BaseSchema`:

```python
class Example(BaseSchema):
    example_id: int
    example_name: str
```

`BaseSchema` включает:

- `from_attributes=True`;
- `alias_generator=camelize`;
- `validate_by_alias=True`;
- `validate_by_name=True`.

В Python-коде поля пишутся в `snake_case`, а наружу в JSON отдаются как `camelCase`.

### 7. Ошибки

Инфраструктурные ошибки БД маппятся в `app/src/exceptions/handler.py`.

Сейчас зарегистрированы handlers для:

- duplicate key;
- foreign key;
- check constraint;
- data integrity;
- database configuration;
- unexpected database errors.

Доменные исключения `DomainError` и `NotFoundError` существуют, но HTTP handlers для них пока не зарегистрированы. Если начинаете активно использовать доменные ошибки, сначала добавьте и зарегистрируйте соответствующие exception handlers.

## Как добавить новую feature

1. Создать директорию `app/src/features/<feature_name>/`.
2. Добавить `schemas.py`, `repo.py`, `service.py`, `deps.py`, `router.py`.
3. В `schemas.py` описать модели через `BaseSchema`.
4. В `repo.py` создать `<Feature>Repository(BaseRepository)` и вызывать БД через `call_sp()`.
5. В `service.py` создать `<Feature>Service(BaseService)` и держать бизнес-логику там.
6. В `deps.py` собрать dependency chain от `DatabaseConnectionDep` до service.
7. В `router.py` создать `APIRouter` с prefix из `api_prefix_config`.
8. Добавить prefix в `app/src/routers/config.py`.
9. Подключить router в `app/src/routers/v1.py`.

Пример настройки префикса:

```python
class APIV1PrefixConfig:
    prefix: str = "/v1"
    examples: str = "/examples"
```

Пример подключения:

```python
from src.features.example.router import router as example_router

v1_router.include_router(example_router)
```

Итоговый URL строится так:

```text
/api + /v1 + /examples + route_path
```

## Соглашения для ИИ-агентов

Следуйте этим правилам при изменении проекта:

- Не вводить ORM без явного запроса. Текущий паттерн - `asyncpg` и stored functions.
- Не обращаться к БД из `router.py`. Использовать `service.py` и `repo.py`.
- Не смешивать HTTP-логику с репозиториями.
- Использовать абсолютные импорты от `src`, как в существующем коде.
- Запускать локальные команды, связанные с приложением, из директории `app`, если команда импортирует `src`.
- Наследовать API-схемы от `BaseSchema`, но имена полей оставлять такими, как они приходят из БД.
- Для новых endpoint-ов сначала смотреть на `app/src/features/ddu_contractor/` и повторять эту структуру.
- Не запускать data-changing SQL, миграции или скрипты, которые пишут в БД, без явного подтверждения пользователя.
- Не коммитить `app/.env` и другие секреты.
- Не добавлять глобальные абстракции, пока есть только один-два конкретных use case.
- Если добавляете доменные ошибки, добавьте FastAPI handlers, иначе они уйдут как 500.

## Тесты и линтеры

На данный момент в репозитории не найдено настроенных тестов, Ruff, Black, mypy, pre-commit или CI workflow.

Если добавляете их, фиксируйте команды здесь, чтобы следующие разработчики и ИИ-агенты знали стандартную проверку проекта.

Рекомендуемая будущая секция:

```bash
# tests
pytest

# lint
ruff check .

# format
ruff format .
```

## Важные замечания

- `prestart.sh` содержит `pogo apply`, но Dockerfile сейчас не запускает его как entrypoint.
- Миграций и `pogo`-конфига в репозитории сейчас нет.
- CORS origins захардкожены в `app/src/config.py` на `localhost:3000` и `127.0.0.1:3000`.
- Gunicorn по умолчанию слушает `0.0.0.0:8000`.
- Единственный полноценный пример бизнес-модуля сейчас - `ddu_contractor`; используйте его как шаблон.

