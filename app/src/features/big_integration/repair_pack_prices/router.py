from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from .deps import RepairPackPricesServiceDep

router = APIRouter()


@router.post(
    "/repair-pack-prices",
    summary="Цены ремонтных пакетов по списку планировок",
    description=(
        "Принимает `placementUUIDs` (до 10 000 элементов) и возвращает цену подходящего "
        "пакета для каждой планировки. По каждому элементу — свой `status`/`error` в ответе, "
        "один неудачный `placementUUID` не обрывает весь запрос."
    ),
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
