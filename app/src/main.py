from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import close_db_pool, init_db_pool
from src.exceptions import register_infrastructure_handlers
from src.routers import main_router

from .config import cors_config

OPENAPI_TAGS = [
    {
        "name": "Installment (Freedom Finance)",
        "description": (
            "Онлайн-рассрочка Freedom Finance: каталог банковских продуктов, создание и опрос "
            "заявок, входящий webhook о решении банка, автоматический и ручной apply к сделке."
        ),
    },
    {
        "name": "Factoring (Freedom Finance)",
        "description": (
            "Факторинг Freedom Finance: заявки, подготовка печатных форм и электронная подпись "
            "через MyNCA, входящий webhook о статусе."
        ),
    },
    {
        "name": "Big Integration",
        "description": (
            "Legacy-замена Zend `IntegrationController` для интеграций ДДУ. Basic Auth, тело "
            "запроса без Pydantic-валидации (проверки в stored function), ответ в едином "
            "envelope `{\"data\", \"response\", \"error\"}`. `data` — первая строка refcursor "
            "как есть из PostgreSQL, ошибка (500) кладётся в `error.message`."
        ),
    },
    {
        "name": "Health",
        "description": "Проверка живости сервиса (для liveness/readiness probe).",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db_pool()
    yield
    await close_db_pool()


app = FastAPI(
    title="Smart Remont — Integrations",
    summary="Тонкий HTTP-слой над PostgreSQL stored functions для внешних банковских интеграций",
    description=(
        "## Два типа API\n\n"
        "| Тип | Префикс | Auth | Формат ответа |\n"
        "|---|---|---|---|\n"
        "| Внутренний REST | `/api/v1/...` | Basic Auth | Pydantic-схемы, стандартные HTTP-коды |\n"
        "| Big Integration (legacy) | `/api/big_integration/...` | Basic Auth | envelope `{data, response, error}` |\n\n"
        "Вся бизнес-логика и валидация — в PostgreSQL stored functions (`asyncpg`, без ORM); "
        "этот сервис — тонкий транспортный слой поверх них.\n\n"
        "### Провайдеры\n\n"
        "- **Freedom Finance** — онлайн-рассрочка (`installment`) и факторинг (`factoring`), "
        "обе заявки хранятся в одной таблице `installment_application_tab` (`product_type`).\n"
        "- **MyNCA** — электронная подпись документов для факторинга.\n"
    ),
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
    openapi_tags=OPENAPI_TAGS,
)
register_infrastructure_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.allow_origins,
    allow_credentials=cors_config.allow_credentials,
    allow_methods=cors_config.allow_methods,
    allow_headers=cors_config.allow_headers,
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Liveness/readiness probe",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(main_router)
