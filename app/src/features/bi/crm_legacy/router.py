from fastapi import Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import LEGACY_BI_RESPONSE
from src.openapi_helpers import integration_controller_description
from .deps import CrmLegacyServiceDep

from fastapi import APIRouter

router = APIRouter()


@router.post(
    "/crm-create-client-request-empty",
    summary="crmCreateClientRequestEmptyAction",
    description=integration_controller_description(
        "**БД:** `rest.bi_create_client_request(flat_guid)`. SP в prod может требовать "
        "доп. аргументы — ошибка вернётся из PostgreSQL.",
        url_action="crm-create-client-request-empty",
        php_method="crmCreateClientRequestEmptyAction",
    ),
    responses=LEGACY_BI_RESPONSE,
)
async def crm_create_client_request_empty(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: CrmLegacyServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.crm_create_client_request_empty(body)


@router.post(
    "/crm-create-client-request-agreement",
    summary="crmCreateClientRequestAgreementAction",
    description=integration_controller_description(
        "**БД:** `rest.bi_create_client_request_agreement` (может отсутствовать в pg_proc).",
        url_action="crm-create-client-request-agreement",
        php_method="crmCreateClientRequestAgreementAction",
    ),
    responses=LEGACY_BI_RESPONSE,
)
async def crm_create_client_request_agreement(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: CrmLegacyServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.crm_create_client_request_agreement(body)


@router.post(
    "/create-request",
    summary="createRequestAction",
    description=integration_controller_description(
        "**БД:** `rest.bi_create_request` → `rest.bi_get_client_request_material_json`. "
        "SP может отсутствовать в pg_proc.",
        url_action="create-request",
        php_method="createRequestAction",
    ),
    responses=LEGACY_BI_RESPONSE,
)
async def create_request(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: CrmLegacyServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.create_request(body)


@router.post(
    "/sr-remont-report",
    summary="srRemontReportAction",
    description=integration_controller_description(
        "**БД:** `rest.sr_remont_report` (может отсутствовать в pg_proc).",
        url_action="sr-remont-report",
        php_method="srRemontReportAction",
    ),
    responses=LEGACY_BI_RESPONSE,
)
async def sr_remont_report(
    _: BigIntegrationBasicAuthDep,
    service: CrmLegacyServiceDep,
) -> JSONResponse:
    return await service.sr_remont_report()
