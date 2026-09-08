from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from src.openapi_helpers import add_cron_route, cron_description, legacy_integration_path

from .deps import WorkersServiceDep
from .errors import WorkersDatabaseError

router = APIRouter(tags=["Workers / Cron / BI sync"])


@router.get(
    "/flat-list",
    summary="flatListAction — BI placements → flat_upd",
    description=(
        "**Query:** `guid` (block GUID, через `;` для нескольких).\n"
        "**БД:** `public.flat_upd` после BI API."
        + legacy_integration_path("flat-list")
    ),
)
async def flat_list(
    service: WorkersServiceDep,
    guid: str = Query(""),
) -> JSONResponse:
    try:
        return JSONResponse(await service.flat_list(guid))
    except WorkersDatabaseError as exc:
        return JSONResponse({"status": False, "error": exc.message}, status_code=500)


@add_cron_route(
    router,
    "/send-bi-process",
    summary="Cron: sendBiProcessAction — integration_tab → BI CRM",
    description=cron_description(
        "`public.integration_tab__read` → POST BI CRM → `integration_tab__set_send` / `_set_error`.",
        php_action="send-bi-process",
    ),
)
async def send_bi_process(service: WorkersServiceDep) -> Response:
    try:
        return PlainTextResponse(await service.send_bi_process())
    except WorkersDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)


@add_cron_route(
    router,
    "/bi-resident-sync",
    summary="Cron: biResidentSyncAction — residents → 1C",
    description=cron_description(
        "BI GetObjectsList → `public.resident_1c_sync_upd` + `resident_1c_sync`.",
        php_action="bi-resident-sync",
    ),
)
async def bi_resident_sync(service: WorkersServiceDep) -> Response:
    try:
        return PlainTextResponse(await service.bi_resident_sync())
    except WorkersDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)


@add_cron_route(
    router,
    "/flat-sync-auto",
    summary="Cron: flatSyncAutoAction — auto flat sync",
    description=cron_description(
        "`public.resident_for_flat_sync_read` → BI placements → `public.flat_upd`.",
        php_action="flat-sync-auto",
    ),
)
async def flat_sync_auto(service: WorkersServiceDep) -> Response:
    try:
        return PlainTextResponse(await service.flat_sync_auto())
    except WorkersDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)


@add_cron_route(
    router,
    "/pdf-find-sum",
    summary="Cron: pdfFindSumAction — проверка суммы в PDF",
    description=cron_description(
        "`public.parse_pdf__read_agreement` → download PDF → pypdf → `parse_pdf__process_agreement`.",
        php_action="pdf-find-sum",
    ),
)
async def pdf_find_sum(service: WorkersServiceDep) -> Response:
    try:
        return PlainTextResponse(await service.pdf_find_sum())
    except WorkersDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)


@add_cron_route(
    router,
    "/freedom-auth",
    summary="Cron: freedomAuthAction — FF token refresh",
    description=cron_description(
        "POST FF auth API → `public.freedom_token_upd`. Env `FF_AUTH` / `FF_BASE_URL`.",
        php_action="freedom-auth",
    ),
)
async def freedom_auth(service: WorkersServiceDep) -> Response:
    try:
        return PlainTextResponse(await service.freedom_auth())
    except WorkersDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)
    except Exception as exc:  # noqa: BLE001
        return PlainTextResponse(content=str(exc), status_code=500)


@router.post(
    "/freedom-hook",
    summary="freedomHookAction — webhook (log only)",
    description="Логирует body. Без side effects." + legacy_integration_path("freedom-hook"),
)
async def freedom_hook(request: Request, service: WorkersServiceDep) -> JSONResponse:
    body = await request.body()
    return JSONResponse(await service.freedom_hook(body))


@add_cron_route(
    router,
    "/ddu-request-cancel",
    summary="Cron: dduRequestCancelAction — timeout DDU cancel",
    description=cron_description(
        "`rest.ddu_timeout_request_read` → BIG external cancel API → cancel или renew reserve.",
        php_action="ddu-request-cancel",
    ),
)
async def ddu_request_cancel(service: WorkersServiceDep) -> Response:
    try:
        return PlainTextResponse(await service.ddu_request_cancel())
    except WorkersDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)


@add_cron_route(
    router,
    "/render-job-cron",
    summary="Cron: renderJobCronAction — Planoplan jobs",
    description=cron_description(
        "`rest.pp_read_job` → load_render по planirovka → `pp_job_set_time`. File lock.",
        php_action="render-job-cron",
    ),
)
async def render_job_cron(service: WorkersServiceDep) -> Response:
    try:
        return PlainTextResponse(await service.render_job_cron())
    except WorkersDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)


@router.get(
    "/planoplan",
    summary="planoplanAction — renders для planirovka",
    description=(
        "**Query:** `planirovka_id`. Загрузка скриншотов Planoplan → MinIO → `pp_insert_render`."
        + legacy_integration_path("planoplan")
    ),
)
async def planoplan(
    service: WorkersServiceDep,
    planirovka_id: int = Query(0),
) -> JSONResponse:
    try:
        return JSONResponse(await service.planoplan(planirovka_id))
    except WorkersDatabaseError as exc:
        return JSONResponse({"result": {"status": False, "error": exc.message}}, status_code=500)


@router.get(
    "/planoplan-mode/{mode}",
    summary="planoplanModeAction",
    description=(
        "**mode=all_renders:** query `resident_id` → `pp_insert_job`.\n"
        "**mode=folders_projects:** sync folders/projects."
        + legacy_integration_path("planoplan-mode/{mode}")
    ),
)
async def planoplan_mode(
    service: WorkersServiceDep,
    mode: str,
    request: Request,
) -> JSONResponse:
    params = {k: str(v) for k, v in request.query_params.items()}
    try:
        return JSONResponse(await service.planoplan_mode(mode, params))
    except WorkersDatabaseError as exc:
        return JSONResponse({"result": {"status": False, "error": exc.message}}, status_code=500)


@router.get(
    "/set-folder-name",
    summary="setFolderNameAction — Planoplan folder",
    description=(
        "**Query:** `planirovka_id`, `folder_name` → `rest.pp_update_planirovka_folder`.\n"
        "POST также принимается (скрыт из OpenAPI)."
        + legacy_integration_path("set-folder-name")
    ),
)
@router.post("/set-folder-name", include_in_schema=False)
async def set_folder_name(
    service: WorkersServiceDep,
    planirovka_id: int = Query(0),
    folder_name: str = Query(""),
) -> JSONResponse:
    try:
        return JSONResponse(await service.set_folder_name(planirovka_id, folder_name))
    except WorkersDatabaseError as exc:
        return JSONResponse({"result": {"status": False, "error": exc.message}}, status_code=500)
