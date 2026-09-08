from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_array
from ..openapi_examples import LEGACY_BI_RESPONSE
from .deps import SrStageServiceDep

router = APIRouter()


@router.post(
    "/sr-stage",
    summary="Этап ремонта по списку {iin, id}",
    description=(
        "**БД:** `bi_sr_stage_v3` (вызывается по одному разу на элемент).\n\n"
        'Тело — JSON-массив: `[{"iin": "...", "id": "flat_guid"}, ...]`.'
    ),
    responses=LEGACY_BI_RESPONSE,
)
async def sr_stage(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: SrStageServiceDep,
) -> JSONResponse:
    body = await read_json_array(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.sr_stage(body)
