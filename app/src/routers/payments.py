from fastapi import APIRouter
from src.features.payments.router import router as payments_feature_router

from .config import api_prefix_config

payments_router = APIRouter(prefix=api_prefix_config.payments.prefix)

payments_router.include_router(payments_feature_router)
