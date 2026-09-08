from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

from ..errors import PaymentsDatabaseError
from ..sberbank_client import SberbankClientError
from .deps import SberbankCallbackServiceDep, merge_request_params

router = APIRouter()


@router.api_route(
    "/sberbank-callback",
    methods=["GET", "POST"],
    summary="Sberbank deposit webhook",
    description="Legacy ``sberbankCallbackAction``: callback от Sber → SP + ``insert_sbebank_pay_log``.",
)
async def sberbank_callback(
    request: Request,
    service: SberbankCallbackServiceDep,
) -> Response:
    params = await merge_request_params(request)
    try:
        body = await service.handle({k: v for k, v in params.items()})
        return PlainTextResponse(content=body)
    except (PaymentsDatabaseError, SberbankClientError) as exc:
        return PlainTextResponse(content=getattr(exc, "message", str(exc)), status_code=500)
