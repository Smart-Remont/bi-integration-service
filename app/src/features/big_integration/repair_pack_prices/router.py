from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import REPAIR_PACK_PRICES_BODY, REPAIR_PACK_PRICES_RESPONSE
from .deps import RepairPackPricesServiceDep

router = APIRouter()


@router.post(
    "/repair-pack-prices",
    summary="Цены пакетов",
    description=(
        "**БД:** `ddu_repair_pack_info__get` (на каждый GUID)\n\n"
        "До 10 000 `placementUUIDs`; ошибка по одному элементу не прерывает batch."
    ),
    openapi_extra=REPAIR_PACK_PRICES_BODY,
    responses=REPAIR_PACK_PRICES_RESPONSE,
)
async def repair_pack_prices(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RepairPackPricesServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.repair_pack_prices(body)
