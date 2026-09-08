from fastapi import APIRouter
from src.features.ddu_export.router import router as ddu_export_feature_router

from .config import api_prefix_config

ddu_export_router = APIRouter(prefix=api_prefix_config.ddu_export.prefix)

ddu_export_router.include_router(ddu_export_feature_router)
