from urllib.parse import parse_qsl

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .deps import CallProcessingServiceDep

router = APIRouter()


@router.post(
    "/call-processing",
    summary="Webhook Kcell call processing",
    description=(
        "Kcell шлёт `application/x-www-form-urlencoded`; тело парсится как в PHP "
        "`parse_str` → JSON → `sale.client_call_hist_tab__insert`."
    ),
)
async def call_processing(
    request: Request,
    service: CallProcessingServiceDep,
) -> JSONResponse:
    raw = await request.body()
    try:
        parsed = dict(parse_qsl(raw.decode("utf-8"), keep_blank_values=True))
        result = await service.insert_call_webhook(parsed)
        return JSONResponse(content=result)
    except Exception as exc:
        return JSONResponse(content={"status": False, "error": str(exc)})
