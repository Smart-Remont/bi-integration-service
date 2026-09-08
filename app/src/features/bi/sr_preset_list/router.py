from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import legacy_http_host, read_json_object
from ..openapi_examples import LEGACY_BI_RESPONSE
from src.openapi_helpers import integration_controller_description
from .deps import SrPresetListServiceDep

router = APIRouter()


@router.post(
    "/sr-preset-list",
    summary="Пресеты для BI-приложения по городу",
    description=integration_controller_description(
        "**БД:** `read_preset_for_big_app`\n\n"
        "`host` берётся из адреса самого запроса (как в legacy `getHttpHost()`) — "
        "используется SP для построения абсолютных URL картинок.",
        url_action="sr-preset-list",
        php_method="srPresetListAction",
    ),
    responses=LEGACY_BI_RESPONSE,
)
async def sr_preset_list(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: SrPresetListServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    host = legacy_http_host(request)
    return await service.sr_preset_list(body, host)
