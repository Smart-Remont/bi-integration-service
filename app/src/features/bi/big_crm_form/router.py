from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import LEGACY_BI_RESPONSE
from src.openapi_helpers import integration_controller_description
from .deps import BigCrmFormServiceDep

router = APIRouter()


@router.post(
    "/big-crm-form",
    summary="Лид из BI CRM",
    description=integration_controller_description(
        "**БД:** `crm.request_from_bigcrm`. Тело — произвольный JSON, целиком передаётся в SP.",
        url_action="big-crm-form",
        php_method="bigCrmFormAction",
    ),
    responses=LEGACY_BI_RESPONSE,
)
async def big_crm_form(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: BigCrmFormServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.big_crm_form(body)
