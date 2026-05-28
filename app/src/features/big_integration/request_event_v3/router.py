from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from .deps import RequestEventV3ServiceDep

router = APIRouter()


@router.post("/request-event-v3")
async def request_event_v3(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RequestEventV3ServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.request_event_v3(body)
