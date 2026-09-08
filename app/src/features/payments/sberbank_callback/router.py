from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

from src.openapi_helpers import legacy_integration_path

from ..errors import PaymentsDatabaseError
from ..sberbank_client import SberbankClientError
from .deps import SberbankCallbackServiceDep, merge_request_params

router = APIRouter()


@router.post(
    "/sberbank-callback",
    summary="sberbankCallbackAction — webhook Sber",
    description=(
        "Callback от Sber (query/body) → SP + `insert_sbebank_pay_log`. GET также принимается (скрыт)."
        + legacy_integration_path("sberbank-callback")
    ),
)
@router.get("/sberbank-callback", include_in_schema=False)
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
