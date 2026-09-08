__all__ = ("main_router",)

from fastapi import APIRouter

from .big_integration import big_integration_router
from .config import api_prefix_config
from .ddu_export import ddu_export_router
from .v1 import v1_router

main_router = APIRouter(prefix=api_prefix_config.prefix)

main_router.include_router(v1_router)
main_router.include_router(big_integration_router)
main_router.include_router(ddu_export_router)
