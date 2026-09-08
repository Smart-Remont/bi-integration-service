from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..openapi_examples import LEGACY_BI_RESPONSE
from .deps import SrShowroomReportServiceDep

router = APIRouter()


@router.post(
    "/sr-showroom-report",
    summary="Отчёт по шоуруму",
    description="**БД:** `sr_showroom_report`. Без параметров.",
    responses=LEGACY_BI_RESPONSE,
)
async def sr_showroom_report(
    _: BigIntegrationBasicAuthDep,
    service: SrShowroomReportServiceDep,
) -> JSONResponse:
    return await service.sr_showroom_report()
