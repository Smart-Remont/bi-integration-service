from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference
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
        "name": "BIG Integration",
        "description": (
            "BIG Integration — API ДДУ. Basic Auth (`INTEGRATION_HS_BI_*`). "
            "Имя функции БД — в description операции. `docs/big-integration.md`."
        ),
    },
    {
        "name": "DDU Export",
        "description": (
            "DDU Export — справочники и выгрузки для внешней сверки. Basic Auth "
            "(`DDU_EXPORT_AUTH_*`), отдельные от BIG Integration."
        ),
    },
    {
        "name": "Legacy BI/CRM",
        "description": (
            "Legacy `IntegrationController` (BI-группа): рендер/наличие, отчёты, лиды из "
            "BI-приложения/CRM. Basic Auth — тот же `hs_bi`, что у BIG Integration. "
            "Формат ответа отличается: `error.code`, при ошибке HTTP 400 и `data` содержит "
            "код ошибки `P0xx`. Часть legacy-действий не перенесена — их SP больше нет в БД, "
            "см. `docs/legacy-bi.md`."
        ),
    },
    {
        "name": "Payments",
        "description": (
            "Sber / Forte / Paybox — redirect flows, bank callbacks, status cron. "
            "Credentials: ``SBERBANK_*``, ``FORTE_*`` / DB settings, ``PAYBOX_*``. "
            "Без HTTP auth (как legacy payment actions)."
        ),
    },
    {
        "name": "SMS / Kcell",
        "description": (
            "Cron/webhook SMS и звонков Kcell: очереди `client`/`notify`, poll batch status, "
            "webhook call-processing. Credentials: `KCELL_HERMES_*`, `KCELL_BATCH_*`. "
            "Без HTTP auth (как legacy cron actions)."
        ),
    },
    {
        "name": "File Storage",
        "description": (
            "Async-загрузка файлов напрямую в MinIO (S3). Контракт `{filename, path, ext}` "
            "совместим с myspace `file_store()`. Неизвестный `mode` → HTTP 400. Env: `MINIO_*`, "
            "`STORAGE_PUBLIC_URL`."
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
        "| BIG Integration | `/api/big_integration/...` | Basic Auth | envelope `{data, response, error}` |\n\n"
        "Вся бизнес-логика и валидация — в PostgreSQL stored functions (`asyncpg`, без ORM); "
        "этот сервис — тонкий транспортный слой поверх них.\n\n"
        "### Провайдеры\n\n"
        "- **Freedom Finance** — онлайн-рассрочка (`installment`) и факторинг (`factoring`), "
        "обе заявки хранятся в одной таблице `installment_application_tab` (`product_type`).\n"
        "- **MyNCA** — электронная подпись документов для факторинга.\n"
        "- **BIG Integration** — API ДДУ (`/api/big_integration/...`, см. `docs/big-integration.md`).\n"
        "- **DDU Export** — справочники ДДУ (`/api/ddu_export/...`), отдельный Basic Auth.\n"
        "- **Legacy BI/CRM** — `/api/legacy_bi/...`, см. `docs/legacy-bi.md`.\n"
        "- **SMS / Kcell** — cron `/api/sms/...` (Hermes + batch poll + call webhook).\n"
        "- **Payments** — Sber/Forte/Paybox `/api/payments/...`.\n"
        "- **File Storage** — прямой MinIO для `/documents/...` (`MINIO_*`, `STORAGE_PUBLIC_URL`).\n"
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


@app.get("/scalar", include_in_schema=False)
async def scalar_docs() -> HTMLResponse:
    return get_scalar_api_reference(
        openapi_url=app.openapi_url or "/openapi.json",
        title=app.title,
        telemetry=False,
    )


app.include_router(main_router)
