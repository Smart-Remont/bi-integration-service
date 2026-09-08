from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object_ru
from ..preset.validators import validate_placement_uuid
from ..responses import big_integration_error_response
from .deps import RemontPresetListV2ServiceDep

router = APIRouter()

_METHOD_NOT_ALLOWED = "Неподдерживаемый метод"


@router.post(
    "/remont-preset-list-v2",
    summary="Список пресетов с наполнением и рендерами",
    description=(
        "**БД:** `ddu__preset_list_v2`, `render_plan_room__read`, "
        "`render_preset_feature*`, `render_filling__*`, `render__read`"
    ),
)
async def remont_preset_list_v2(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RemontPresetListV2ServiceDep,
) -> JSONResponse:
    body = await read_json_object_ru(request)
    if isinstance(body, JSONResponse):
        return body

    placement_error = validate_placement_uuid(body)
    if placement_error is not None:
        return placement_error

    return await service.remont_preset_list_v2(body)


@router.api_route(
    "/remont-preset-list-v2",
    methods=["GET", "HEAD", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def remont_preset_list_v2_method_not_allowed() -> JSONResponse:
    return big_integration_error_response(
        _METHOD_NOT_ALLOWED,
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    )
