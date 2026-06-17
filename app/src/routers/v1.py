from fastapi import APIRouter
from src.features.ddu_contractor.router import router as ddu_contractor_router
from src.features.installment.router import router as installment_router

from .config import api_prefix_config

v1_router = APIRouter(prefix=api_prefix_config.v1.prefix)

v1_router.include_router(ddu_contractor_router)
v1_router.include_router(installment_router)
