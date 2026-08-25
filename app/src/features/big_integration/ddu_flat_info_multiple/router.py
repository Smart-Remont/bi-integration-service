from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from .deps import DduFlatInfoMultipleServiceDep

router = APIRouter()


@router.post(
    "/ddu-flat-info-multiple",
    summary="Информация по нескольким квартирам ДДУ",
    description=(
        "Принимает список `flat_guids` и возвращает информацию по каждой квартире "
        "(`sp: rest.ddu_flat_info_multiple`). `flat_guids` обязателен и не может быть пустым."
    ),
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
