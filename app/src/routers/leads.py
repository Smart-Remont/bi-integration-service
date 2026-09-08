from fastapi import APIRouter
from src.features.leads.router import router as leads_feature_router

from .config import api_prefix_config

leads_router = APIRouter(prefix=api_prefix_config.leads.prefix)

leads_router.include_router(leads_feature_router)
