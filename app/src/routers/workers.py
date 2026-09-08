from fastapi import APIRouter
from src.features.workers.router import router as workers_feature_router

from .config import api_prefix_config

workers_router = APIRouter(prefix=api_prefix_config.workers.prefix)

workers_router.include_router(workers_feature_router)
