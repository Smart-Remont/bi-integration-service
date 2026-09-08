from collections.abc import Awaitable
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from src.http_response_utils import get_error_message, plain_from
from src.openapi_helpers import add_cron_route, cron_description, legacy_integration_path

from .deps import LeadsServiceDep
from .errors import LeadsDatabaseError

router = APIRouter(tags=["Leads / Tilda / Forms"])


async def _plain(result: Awaitable[str]) -> PlainTextResponse:
    return await plain_from(result, db_error=LeadsDatabaseError)


async def _json_status(result: Awaitable[dict[str, Any]]) -> JSONResponse:
    try:
        return JSONResponse(await result)
    except LeadsDatabaseError as exc:
        return JSONResponse({"status": False, "error": get_error_message(exc)}, status_code=500)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"status": False, "error": get_error_message(exc)}, status_code=500)


@router.post(
    "/tilda-form",
    summary="Webhook формы Tilda",
    description=(
        "`crm.request_from_tilda` — urlencoded body. Ответ: `ok`."
        + legacy_integration_path("tilda-form")
    ),
)
async def tilda_form(request: Request, service: LeadsServiceDep) -> Response:
    body = await request.body()
    return await _plain(service.tilda_form(body))


@router.post(
    "/facebook-form",
    summary="Webhook формы Facebook",
    description=(
        "``crm.request_from_fb`` — JSON body. Ответ: ``\"ok\"``."
        + legacy_integration_path("facebook-form")
    ),
)
async def facebook_form(request: Request, service: LeadsServiceDep) -> Response:
    body = await request.body()
    return await _plain(service.facebook_form(body))


@router.post(
    "/albato-meta-lead",
    summary="Albato Meta lead webhook",
    description=(
        "``crm.request_from_albato_meta``. Query ``token`` = ``ALBATO_META_TOKEN``."
        + legacy_integration_path("albato-meta-lead")
    ),
)
async def albato_meta_lead(
    request: Request,
    service: LeadsServiceDep,
    token: str = Query(""),
) -> JSONResponse:
    try:
        body = await request.body()
        status_code, payload = await service.albato_meta_lead(token=token, raw_body=body)
        return JSONResponse(payload, status_code=status_code)
    except LeadsDatabaseError as exc:
        return JSONResponse({"error": get_error_message(exc)}, status_code=500)


@router.get(
    "/image-search",
    summary="Поиск картинок (legacy Google scrape)",
    description=(
        "Legacy ``imageSearchFormAction`` — JSON ``{images: [src,...]}`` вместо HTML view."
        + legacy_integration_path("image-search")
    ),
)
async def image_search(
    service: LeadsServiceDep,
    query: str = Query(""),
) -> JSONResponse:
    images = await service.image_search(query)
    return JSONResponse({"images": images})


@router.get(
    "/tilda-api-webhook",
    summary="tildaApiWebhookAction — Tilda publish webhook",
    description=(
        "`public.tilda_webhook_insert` — query `pageid`, `projectid`, `published`.\n"
        "POST также принимается (скрыт из OpenAPI)."
        + legacy_integration_path("tilda-api-webhook")
    ),
)
@router.post("/tilda-api-webhook", include_in_schema=False)
async def tilda_api_webhook(request: Request, service: LeadsServiceDep) -> Response:
    params = {k: str(v) for k, v in request.query_params.items()}
    return await _plain(service.tilda_api_webhook(params))


@router.get(
    "/tilda-project-list",
    summary="Список проектов Tilda",
    description=(
        "``mode=get_projects`` — sync из Tilda API → ``tilda_project_insert``. Иначе — read из БД."
        + legacy_integration_path("tilda-project-list")
    ),
)
async def tilda_project_list(
    service: LeadsServiceDep,
    mode: str = Query(""),
) -> JSONResponse:
    return await _json_status(service.tilda_project_list(mode))


@router.get(
    "/tilda-api",
    summary="tildaApiAction — экспорт проекта Tilda",
    description=(
        "**Query:** `project_id`. Env `TILDA_EXPORT_DIR`.\n"
        "POST также принимается (скрыт из OpenAPI)."
        + legacy_integration_path("tilda-api")
    ),
)
@router.post("/tilda-api", include_in_schema=False)
async def tilda_api(
    service: LeadsServiceDep,
    project_id: int = Query(0),
) -> JSONResponse:
    return await _json_status(service.tilda_api_export(project_id))


@add_cron_route(
    router,
    "/tilda-webhook-pages",
    summary="Cron: tildaWebhookPagesAction — очередь Tilda webhook",
    description=cron_description(
        "`tilda_webhook_read` → export pages → `tilda_webhook_set_downloaded`.",
        php_action="tilda-webhook-pages",
    ),
)
async def tilda_webhook_pages(service: LeadsServiceDep) -> Response:
    return await _plain(service.tilda_webhook_pages())
