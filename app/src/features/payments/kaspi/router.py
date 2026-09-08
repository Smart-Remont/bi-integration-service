from fastapi import APIRouter, Request
from fastapi.responses import Response

from src.openapi_helpers import legacy_client_path

from .deps import KaspiServiceDep
from .ip import client_ip

router = APIRouter()

_DESC_REQUEST = (
    "Kaspi check/pay по заявке (`type=1`). Query: `command`, `txn_id`, `iin`, `account`, `sum`, "
    "`txn_date` (pay). Ответ XML UTF-8. IP allowlist: `KASPI_ALLOWED_IPS`."
    + legacy_client_path("kaspi-request-pay")
)

_DESC_PAYMENT = (
    "Kaspi check/pay по платежу (`type=2`). Query: `command`, `txn_id`, `iin`, `account`, `sum`, "
    "`txn_date` (pay). Ответ XML UTF-8. IP allowlist: `KASPI_ALLOWED_IPS`."
    + legacy_client_path("kaspi-payment-pay")
)


@router.get(
    "/kaspi-request-pay",
    summary="kaspiRequestPayAction",
    description=_DESC_REQUEST,
    response_class=Response,
)
@router.post("/kaspi-request-pay", include_in_schema=False)
async def kaspi_request_pay(
    request: Request,
    service: KaspiServiceDep,
) -> Response:
    params = dict(request.query_params)
    xml, status_code = await service.handle_request_pay(
        client_ip=client_ip(request),
        params=params,
    )
    return Response(content=xml, media_type="text/xml; charset=utf-8", status_code=status_code)


@router.get(
    "/kaspi-payment-pay",
    summary="kaspiPaymentPayAction",
    description=_DESC_PAYMENT,
    response_class=Response,
)
@router.post("/kaspi-payment-pay", include_in_schema=False)
async def kaspi_payment_pay(
    request: Request,
    service: KaspiServiceDep,
) -> Response:
    params = dict(request.query_params)
    xml, status_code = await service.handle_payment_pay(
        client_ip=client_ip(request),
        params=params,
    )
    return Response(content=xml, media_type="text/xml; charset=utf-8", status_code=status_code)
