from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import (
    DDU_FLAT_INFO_MULTIPLE_BODY,
    DDU_FLAT_INFO_MULTIPLE_RESPONSE,
)
from .deps import DduFlatInfoMultipleServiceDep

router = APIRouter()


@router.post(
    "/ddu-flat-info-multiple",
    summary="Заявки по списку квартир",
    description=(
        "**БД:** `ddu_flat_info_multiple`\n\n"
        "Тело: `{ \"flat_guids\": [...] }`, массив обязателен."
    ),
    openapi_extra=DDU_FLAT_INFO_MULTIPLE_BODY,
    responses=DDU_FLAT_INFO_MULTIPLE_RESPONSE,
)
async def ddu_flat_info_multiple(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: DduFlatInfoMultipleServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.ddu_flat_info_multiple(body)
