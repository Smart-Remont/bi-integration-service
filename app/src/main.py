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
        "name": "IntegrationController (hs_bi)",
        "description": (
            "PHP ``IntegrationController`` (hs_bi): ``sr-render``, ``remont-avail``, ``bigapp-form``. "
            "Basic Auth ``INTEGRATION_HS_BI_*``. Конверт ``response_json()`` — HTTP 400, ``P0xx``. "
            "URL: ``/api/integration/{action}``. См. docs/bi.md."
        ),
    },
    {
        "name": "Payments",
        "description": (
            "Sber / Forte / Paybox — redirect flows, bank callbacks, status cron. "
            "Cron `sberbank-check-payment-status` — **GET в OpenAPI**, POST скрыт. "
            "Credentials: ``SBERBANK_*``, ``FORTE_*`` / DB settings, ``PAYBOX_*``. "
            "Без HTTP auth (как legacy payment actions)."
        ),
    },
    {
        "name": "SMS / Kcell",
        "description": (
            "Cron/webhook Kcell. **Cron-роуты в OpenAPI — только GET**; POST работает, но скрыт "
            "(как legacy PHP). Env: `KCELL_HERMES_*`, `KCELL_BATCH_*`. Без HTTP auth."
        ),
    },
    {
        "name": "Signing (Aitu / DID / MyNCA)",
        "description": (
            "Legacy `IntegrationController` signing: Aitu OAuth, cron poll подписей, PDF download. "
            "**Cron в OpenAPI — GET**; POST скрыт, handler тот же. PHP: `/integration/{action}`. "
            "Без auth. Env: `AITU_*`, `MYNCA_*`, `SIGNING_PUBLIC_BASE_URL`."
        ),
    },
    {
        "name": "Leads / Tilda / Forms",
        "description": (
            "Webhook-формы Tilda/Facebook/Albato Meta, экспорт Tilda на диск, cron обработки "
            "webhook-очереди. Env: ``ALBATO_META_TOKEN``, ``TILDA_EXPORT_DIR``. Без HTTP auth."
        ),
    },
    {
        "name": "Workers / Cron / BI sync",
        "description": (
            "Planoplan, BI sync, DDU cancel, Freedom. **Cron — GET в OpenAPI**, POST скрыт. "
            "PHP: `/integration/{action}`. Без auth."
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
        "## Cutover с PHP `IntegrationController`\n\n"
        "Legacy URL: `/integration/{action}` → этот сервис: `/api/{module}/{action}`.\n\n"
        "| Модуль | Префикс | Auth |\n"
        "|---|---|---|\n"
        "| BIG Integration | `/api/big_integration/` | Basic `hs_bi` |\n"
        "| IntegrationController (hs_bi) | `/api/integration/` | Basic `hs_bi` |\n"
        "| DDU Export | `/api/ddu_export/` | Basic `ddu_export` |\n"
        "| Signing / SMS / Workers / Leads | `/api/signing/` … | нет |\n\n"
        "### Cron и GET+POST\n\n"
        "У cron-роутов (SMS, signing, workers) **в Swagger/Scalar один метод — GET**. "
        "**POST принимается** тем же кодом, но **скрыт из схемы**, чтобы не дублировать операции. "
        "В PHP метод не проверялся — для crontab достаточно `curl` GET.\n\n"
        "Документация: `/scalar`, `/docs`, `docs/README.md`.\n"
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
