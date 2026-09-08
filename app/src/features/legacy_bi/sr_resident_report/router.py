from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..openapi_examples import LEGACY_BI_RESPONSE
from .deps import SrResidentReportServiceDep

router = APIRouter()


@router.post(
    "/sr-resident-report",
    summary="Отчёт по жильцам",
    description="**БД:** `sr_resident_report`. Без параметров.",
    responses=LEGACY_BI_RESPONSE,
)
async def sr_resident_report(
    _: BigIntegrationBasicAuthDep,
    service: SrResidentReportServiceDep,
) -> JSONResponse:
    return await service.sr_resident_report()
