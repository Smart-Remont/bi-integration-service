from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object_ru
from ..preset.validators import validate_placement_uuid, validate_preset_id
from ..responses import big_integration_error_response
from .deps import RemontPresetServiceDep

router = APIRouter()

_METHOD_NOT_ALLOWED = "Неподдерживаемый метод"


@router.post(
    "/remont-preset",
    summary="Пресет с ценами наполнения",
    description=(
        "**БД:** `ddu__preset_list_v2`, `render_filling__section__read`, "
        "`render_filling__*` (компактные sets)"
    ),
)
async def remont_preset(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RemontPresetServiceDep,
) -> JSONResponse:
    body = await read_json_object_ru(request)
    if isinstance(body, JSONResponse):
        return body

    placement_error = validate_placement_uuid(body)
    if placement_error is not None:
        return placement_error

    preset_error = validate_preset_id(body)
    if preset_error is not None:
        return preset_error

    return await service.remont_preset(body)


@router.api_route(
    "/remont-preset",
    methods=["GET", "HEAD", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def remont_preset_method_not_allowed() -> JSONResponse:
    return big_integration_error_response(
        _METHOD_NOT_ALLOWED,
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    )
