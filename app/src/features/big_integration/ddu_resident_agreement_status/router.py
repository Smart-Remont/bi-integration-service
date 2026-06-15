from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from .deps import DduResidentAgreementStatusServiceDep

router = APIRouter()


@router.post("/ddu-resident-agreement-status")
async def ddu_resident_agreement_status(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: DduResidentAgreementStatusServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.ddu_resident_agreement_status(body)
