from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..openapi_examples import SR_RESIDENT_REPORT_RESPONSE
from src.openapi_helpers import integration_controller_description
from .deps import SrResidentReportServiceDep

router = APIRouter()


@router.post(
    "/sr-resident-report",
    summary="Отчёт по жильцам",
    description=integration_controller_description(
        "**БД:** `sr_resident_report`. Без параметров.",
        url_action="sr-resident-report",
        php_method="srResidentReportAction",
    ),
    responses=SR_RESIDENT_REPORT_RESPONSE,
)
async def sr_resident_report(
    _: BigIntegrationBasicAuthDep,
    service: SrResidentReportServiceDep,
) -> JSONResponse:
    return await service.sr_resident_report()
