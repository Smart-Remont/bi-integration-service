from fastapi import APIRouter
from src.features.legacy_bi.router import router as legacy_bi_feature_router

from .config import api_prefix_config

legacy_bi_router = APIRouter(prefix=api_prefix_config.legacy_bi.prefix)

legacy_bi_router.include_router(legacy_bi_feature_router)
