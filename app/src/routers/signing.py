from fastapi import APIRouter
from src.features.signing.router import router as signing_feature_router

from .config import api_prefix_config

signing_router = APIRouter(prefix=api_prefix_config.signing.prefix)

signing_router.include_router(signing_feature_router)
