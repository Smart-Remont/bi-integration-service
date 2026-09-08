from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import (
    DDU_RESIDENT_AGREEMENT_BODY,
    DDU_RESIDENT_AGREEMENT_RESPONSE,
)
from .deps import DduResidentAgreementStatusServiceDep

router = APIRouter()


@router.post(
    "/ddu-resident-agreement-status",
    summary="Статус договора жильца",
    description="**БД:** `ddu_resident_agreement__log_insert`",
    openapi_extra=DDU_RESIDENT_AGREEMENT_BODY,
    responses=DDU_RESIDENT_AGREEMENT_RESPONSE,
)
async def ddu_resident_agreement_status(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: DduResidentAgreementStatusServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.ddu_resident_agreement_status(body)
