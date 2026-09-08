from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import LEGACY_BI_RESPONSE
from .deps import BigappFormServiceDep

router = APIRouter()


@router.post(
    "/bigapp-form",
    summary="Лид из BI-приложения",
    description="**БД:** `crm.request_from_bigapp`. Тело — произвольный JSON, целиком передаётся в SP.",
    responses=LEGACY_BI_RESPONSE,
)
async def bigapp_form(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: BigappFormServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.bigapp_form(body)
