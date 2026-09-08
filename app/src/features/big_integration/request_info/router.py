from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..openapi_examples import REQUEST_INFO_RESPONSE
from .deps import RequestInfoServiceDep

router = APIRouter()


@router.get(
    "/request-info",
    summary="Заявка по ID ДДУ",
    description=(
        "**БД:** `ddu_request_info`\n\n"
        "Query: `deal_id`, `application_id`, `order_id`. "
        "Пустые значения передаются как NULL."
    ),
    responses=REQUEST_INFO_RESPONSE,
)
async def request_info(
    _: BigIntegrationBasicAuthDep,
    service: RequestInfoServiceDep,
    deal_id: str = Query(default="", description="ID сделки ДДУ"),
    application_id: str = Query(default="", description="ID заявки ДДУ"),
    order_id: str = Query(default="", description="ID заказа ДДУ"),
) -> JSONResponse:
    return await service.request_info(deal_id, application_id, order_id)
