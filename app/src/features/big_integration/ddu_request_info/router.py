from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..openapi_examples import REQUEST_INFO_RESPONSE
from .deps import DduRequestInfoServiceDep

router = APIRouter()


@router.get(
    "/ddu-request-info",
    summary="Заявка по client_request_id",
    description=(
        "**БД:** `ddu_request_info_by_client_request`\n\n"
        "Query: `client_request_id` (0 → NULL)."
    ),
    responses=REQUEST_INFO_RESPONSE,
)
async def ddu_request_info(
    _: BigIntegrationBasicAuthDep,
    service: DduRequestInfoServiceDep,
    client_request_id: int = Query(
        default=0,
        description="ID заявки Smart Remont",
    ),
) -> JSONResponse:
    return await service.ddu_request_info(client_request_id)
