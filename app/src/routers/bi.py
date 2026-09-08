from fastapi import APIRouter
from src.features.bi.router import router as bi_feature_router

from .config import api_prefix_config

bi_router = APIRouter(prefix=api_prefix_config.bi.prefix)

bi_router.include_router(bi_feature_router)
