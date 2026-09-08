from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import (
    CHANGE_REQUEST_STATUS_BODY,
    CHANGE_REQUEST_STATUS_RESPONSE,
)
from src.openapi_helpers import integration_controller_description
from .deps import ChangeRequestStatusServiceDep

router = APIRouter()


@router.post(
    "/change-request-status",
    summary="Изменить статус заявки BI",
    description=integration_controller_description(
        '**БД:** `bi_change_request_status`. Тело: `{"application_id": ..., "status_code": "..."}`.',
        url_action="change-request-status",
        php_method="changeRequestStatusAction",
    ),
    openapi_extra=CHANGE_REQUEST_STATUS_BODY,
    responses=CHANGE_REQUEST_STATUS_RESPONSE,
)
async def change_request_status(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: ChangeRequestStatusServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.change_request_status(body)
