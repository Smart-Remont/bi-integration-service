from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import (
    BIGAPP_FORM_BODY,
    BIGAPP_FORM_RESPONSE,
)
from src.openapi_helpers import integration_controller_description
from .deps import BigappFormServiceDep

router = APIRouter()


@router.post(
    "/bigapp-form",
    summary="Лид из BI-приложения",
    description=integration_controller_description(
        "**БД:** `crm.request_from_bigapp`. Тело — произвольный JSON, целиком передаётся в SP.",
        url_action="bigapp-form",
        php_method="bigappFormAction",
    ),
    openapi_extra=BIGAPP_FORM_BODY,
    responses=BIGAPP_FORM_RESPONSE,
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
