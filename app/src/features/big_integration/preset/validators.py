from fastapi import status
from fastapi.responses import JSONResponse

from ..responses import big_integration_error_response

_EMPTY_PLACEMENT_UUID = "ГУИД помещения не может быть пустым"
_EMPTY_PRESET_ID = "preset_id не может быть пустым"


def _is_php_empty(value: object | None) -> bool:
    """Match PHP ``empty()`` + ``strlen(trim()) === 0`` checks from IntegrationController."""
    if value is None:
        return True
    if value is False or value == 0:
        return True
    if isinstance(value, str):
        if value == "0" or len(value.strip()) == 0:
            return True
        return False
    if isinstance(value, (list, dict, tuple)) and len(value) == 0:
        return True
    return False


def validate_placement_uuid(body: dict[str, object]) -> JSONResponse | None:
    placement_uuid = body.get("placementUUID")
    if _is_php_empty(placement_uuid):
        return big_integration_error_response(
            _EMPTY_PLACEMENT_UUID,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return None


def validate_preset_id(body: dict[str, object]) -> JSONResponse | None:
    preset_id = body.get("preset_id")
    if _is_php_empty(preset_id):
        return big_integration_error_response(
            _EMPTY_PRESET_ID,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return None
