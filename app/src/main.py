from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import close_db_pool, init_db_pool
from src.exceptions import register_infrastructure_handlers
from src.routers import main_router

from .config import cors_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db_pool()
    yield
    await close_db_pool()


app = FastAPI(
    title="integrations-sr",
    description="HTTP-слой над PostgreSQL stored functions: внутренний API `/api/v1` и legacy big integration.",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
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
