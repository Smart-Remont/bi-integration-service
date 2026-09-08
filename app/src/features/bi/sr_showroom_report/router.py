from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..openapi_examples import SR_SHOWROOM_REPORT_RESPONSE
from src.openapi_helpers import integration_controller_description
from .deps import SrShowroomReportServiceDep

router = APIRouter()


@router.post(
    "/sr-showroom-report",
    summary="Отчёт по шоуруму",
    description=integration_controller_description(
        "**БД:** `sr_showroom_report`. Без параметров.",
        url_action="sr-showroom-report",
        php_method="srShowroomReportAction",
    ),
    responses=SR_SHOWROOM_REPORT_RESPONSE,
)
async def sr_showroom_report(
    _: BigIntegrationBasicAuthDep,
    service: SrShowroomReportServiceDep,
) -> JSONResponse:
    return await service.sr_showroom_report()
