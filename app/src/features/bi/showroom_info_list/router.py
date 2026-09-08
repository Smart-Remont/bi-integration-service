from fastapi import APIRouter, Response

from src.openapi_helpers import legacy_integration_path

from .deps import ShowroomInfoListServiceDep

router = APIRouter()


@router.get(
    "/showroom-info-list",
    summary="showroomInfoListAction — proxy в BI Opera",
    description=(
        "**БД:** `rest.read_marketing_remont_list()` → POST JSON в "
        "`BI_SHOWROOM_INFO_URL` (default opera.bi.group). **Auth:** нет."
        + legacy_integration_path("showroom-info-list")
    ),
)
@router.post("/showroom-info-list", include_in_schema=False)
async def showroom_info_list(service: ShowroomInfoListServiceDep) -> Response:
    body, status_code = await service.proxy()
    media_type = "application/json" if body.strip().startswith(("{", "[")) else "text/plain"
    return Response(content=body, media_type=media_type, status_code=status_code)
