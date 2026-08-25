from fastapi import APIRouter
from src.routers import api_prefix_config

from .deps import DduContractorServiceDep

router = APIRouter(
    prefix=api_prefix_config.v1.ddu_contractors,
    tags=["DDU Contractors"],
    include_in_schema=False,  # internal-only, not part of the public /docs surface
)


@router.get("/", summary="Список подрядчиков ДДУ")
async def list_ddu_contractors(ddu_service_contractor: DduContractorServiceDep):
    return await ddu_service_contractor.list_ddu_contractor()
