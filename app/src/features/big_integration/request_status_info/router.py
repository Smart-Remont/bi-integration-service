from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..openapi_examples import REQUEST_INFO_RESPONSE
from .deps import RequestStatusInfoServiceDep

router = APIRouter()


@router.get(
    "/request-status-info",
    summary="Заявка и статус",
    description=(
        "**БД:** `ddu_request_and_status_info`\n\n"
        "Query: `deal_id`, `application_id`, `order_id`."
    ),
    responses=REQUEST_INFO_RESPONSE,
)
async def request_status_info(
    _: BigIntegrationBasicAuthDep,
    service: RequestStatusInfoServiceDep,
    deal_id: str = Query(default="", description="ID сделки ДДУ"),
    application_id: str = Query(default="", description="ID заявки ДДУ"),
    order_id: str = Query(default="", description="ID заказа ДДУ"),
) -> JSONResponse:
    return await service.request_status_info(deal_id, application_id, order_id)
