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
        "description": "Онлайн-рассрочка FF: каталог продуктов, заявки, webhook, apply к сделке.",
    },
    {
        "name": "Factoring (Freedom Finance)",
        "description": "Факторинг FF: заявки, печатные формы с ЭЦП (MyNCA), webhook.",
    },
    {
        "name": "DDU Contractors",
        "description": "Справочник подрядчиков ДДУ.",
    },
    {
        "name": "Big Integration",
        "description": "Legacy-замена Zend `IntegrationController`: Basic Auth, envelope `data/response/error`.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db_pool()
    yield
    await close_db_pool()


app = FastAPI(
    title="Smart Remont — Integrations",
    description=(
        "HTTP-слой над PostgreSQL stored functions: внутренний REST API `/api/v1` "
        "(installment, factoring, ddu_contractors) и legacy big integration `/api/big_integration`."
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(main_router)
