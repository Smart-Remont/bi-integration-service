from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object_ru
from .deps import RemontPresetListServiceDep

router = APIRouter()


@router.post(
    "/remont-preset-list",
    summary="Список пресетов по помещению (legacy v1)",
    description=(
        "Legacy-совместимость: **БД:** `ddu__preset_list` (старее, чем "
        "`remont-preset-list-v2`'s `ddu__preset_list_v2`). Требует непустой `placementUUID`."
    ),
    deprecated=True,
)
async def remont_preset_list(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RemontPresetListServiceDep,
) -> JSONResponse:
    body = await read_json_object_ru(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.remont_preset_list(body)
