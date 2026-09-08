from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import LEGACY_BI_RESPONSE
from .deps import GetConstructivesServiceDep

router = APIRouter()


@router.post(
    "/get-constructives",
    summary="Конструктив заявки для 1С",
    description='**БД:** `bi_get_client_request_material_json`. Тело: `{"application_id": ...}`.',
    responses=LEGACY_BI_RESPONSE,
)
async def get_constructives(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: GetConstructivesServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.get_constructives(body)
