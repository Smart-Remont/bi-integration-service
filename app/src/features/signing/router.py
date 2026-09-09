from __future__ import annotations

import json
from collections.abc import Awaitable

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.responses import StreamingResponse

from src.http_response_utils import get_error_message, plain_from
from src.openapi_helpers import add_cron_route, cron_description, legacy_integration_path

from .deps import (
    AituFlowServiceDep,
    AituRedirectServiceDep,
    AutoSignOperatorServiceDep,
    DidSignServiceDep,
    MyncaCallbackServiceDep,
    SigningCronServiceDep,
    SigningDownloadServiceDep,
    ThirdPartySignServiceDep,
)
from .errors import SigningDatabaseError
from .openapi_examples import (
    CABINET_ACT_BODY,
    CLIENT_SIGN_BODY,
    MYNCA_CALLBACK_RESPONSES,
    PROJECT_REMONT_BODY,
    THIRD_PARTY_FORM_BODY,
    THIRD_PARTY_RESPONSES,
)

router = APIRouter(tags=["Signing (Aitu / DID / MyNCA)"])


async def _plain(result: Awaitable[str]) -> PlainTextResponse:
    return await plain_from(result, db_error=SigningDatabaseError)


def _pdf_response(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _download_response(result: Awaitable[tuple[bytes, str] | str]) -> Response:
    try:
        output = await result
    except SigningDatabaseError as exc:
        return PlainTextResponse(content=get_error_message(exc), status_code=500)
    except Exception as exc:  # noqa: BLE001
        return PlainTextResponse(content=get_error_message(exc), status_code=400)

    if isinstance(output, str):
        return PlainTextResponse(output)
    pdf_bytes, filename = output
    return _pdf_response(pdf_bytes, filename)


async def _redirect(result: Awaitable[str]) -> Response:
    try:
        url = await result
    except SigningDatabaseError as exc:
        return PlainTextResponse(content=get_error_message(exc), status_code=500)
    except Exception as exc:  # noqa: BLE001
        return PlainTextResponse(content=get_error_message(exc), status_code=400)
    return RedirectResponse(url=url, status_code=302)


@add_cron_route(
    router,
    "/aitu-get-signs",
    summary="Cron: aituGetSignsAction — подписи из Aitu",
    description=cron_description(
        "**БД:** `public.did_read_for_signature` → Aitu `get_signatures(token)` → "
        "совпадение `signableId` → `parseX509Sign` → `public.did_upd` "
        "(signature, signed_xml, dn_name).\n\n"
        "**Ответ:** `0` (text/plain). **Auth:** нет.",
        php_action="aitu-get-signs",
    ),
)
async def aitu_get_signs(service: SigningCronServiceDep) -> Response:
    return await _plain(service.aitu_get_signs())


@add_cron_route(
    router,
    "/aitu-validate-signs",
    summary="Cron: aituValidateSignsAction — верификация подписей",
    description=cron_description(
        "**БД:** `public.did_read_for_verify(did_id)` → Aitu verify → `public.did_upd(is_valid)`.\n\n"
        "**Query:** `did_id` (0 = все записи из очереди). **Ответ:** `0`.",
        php_action="aitu-validate-signs",
    ),
)
async def aitu_validate_signs(
    service: SigningCronServiceDep,
    did_id: int = Query(0, description="0 — обработать всю очередь verify"),
) -> Response:
    return await _plain(service.aitu_validate_signs(did_id))


@add_cron_route(
    router,
    "/aitu-get-photos",
    summary="Cron: aituGetPhotosAction — liveness-фото",
    description=cron_description(
        "**БД:** `public.did_read_for_photo` → Aitu photo API → `public.did_photo_upd`.",
        php_action="aitu-get-photos",
    ),
)
async def aitu_get_photos(service: SigningCronServiceDep) -> Response:
    return await _plain(service.aitu_get_photos())


@add_cron_route(
    router,
    "/aitu-sign-detail",
    summary="Cron: aituSignDetailAction — детали подписи",
    description=cron_description(
        "**БД:** `public.did_read_for_detail` → `AITU_PARSE_URL` → `public.did_detail_insert`.",
        php_action="aitu-sign-detail",
    ),
)
async def aitu_sign_detail(service: SigningCronServiceDep) -> Response:
    return await _plain(service.aitu_sign_detail())


@add_cron_route(
    router,
    "/cron-auto-upload-sign-doc",
    summary="Cron: cronAutoUploadSignDocAction — PDF договора в MinIO",
    description=cron_description(
        "**БД:** `public.sign_read_for_doc` → MyNCA group PDF → MinIO → `sale.sign_document_upd`.",
        php_action="cron-auto-upload-sign-doc",
    ),
)
async def cron_auto_upload_sign_doc(service: SigningCronServiceDep) -> Response:
    return await _plain(service.cron_auto_upload_sign_doc())


@add_cron_route(
    router,
    "/cron-auto-sign-operator",
    summary="Cron: cronAutoSignOperatorAction — CMS автоподпись оператора",
    description=cron_description(
        "**БД:** `public.sign_read_for_auto_sign_operator` → `nca.company_key_store__get_active_by_company` "
        "→ MyNCA `cms/sign-save` → `client.insert_sign_general` → `client.sign_tab__modify`.\n\n"
        "Требует `NCA_MASTER_KEY`, `MYNCA_*`. **Ответ:** `0`.",
        php_action="cron-auto-sign-operator",
    ),
)
async def cron_auto_sign_operator(service: AutoSignOperatorServiceDep) -> Response:
    return await _plain(service.run())


@router.get(
    "/did-sign",
    summary="didSignAction — redirect на Aitu",
    description=(
        "**БД:** `public.did_url_get(state)` → HTTP **302** на Aitu.\n"
        "**Query:** `state`."
        + legacy_integration_path("did-sign")
    ),
)
async def did_sign(
    service: DidSignServiceDep,
    state: str = Query("", description="OAuth state из did_insert"),
) -> Response:
    try:
        url = await service.did_sign_url(state)
    except SigningDatabaseError as exc:
        return PlainTextResponse(content=get_error_message(exc), status_code=500)
    if not url:
        return PlainTextResponse(content="URL not found", status_code=404)
    return RedirectResponse(url=url, status_code=302)


@router.get(
    "/perform-ds-did-sign",
    summary="performDsDidSignAction — старт подписи ДС",
    description=(
        "Office/myspace PDF → MyNCA docx2pdf → `public.did_insert` → redirect Aitu.\n"
        "**Query:** `uuid` (ДС)."
        + legacy_integration_path("perform-ds-did-sign")
    ),
)
async def perform_ds_did_sign(
    service: AituFlowServiceDep,
    uuid: str = Query("", description="UUID доп. соглашения"),
) -> Response:
    return await _redirect(service.perform_ds_did_sign(uuid))


@router.get(
    "/perform-agreement-did-sign",
    summary="performAgreementDidSignAction — старт подписи договора",
    description=(
        "Office contract PDF → MyNCA → `public.did_insert` → redirect Aitu.\n"
        "**Query:** `uuid` (заявка)."
        + legacy_integration_path("perform-agreement-did-sign")
    ),
)
async def perform_agreement_did_sign(
    service: AituFlowServiceDep,
    uuid: str = Query("", description="UUID client_request"),
) -> Response:
    return await _redirect(service.perform_agreement_did_sign(uuid))


@router.get(
    "/aitu-redirect/mode/{mode}",
    summary="aituRedirectAction — OAuth callback Aitu",
    description=(
        "**mode=approve:** query `code`, `state` → token/ИИН → `public.did_upd` → HTML.\n"
        "**mode=logout|logout-callback:** лог, ответ `0`.\n"
        "POST также принимается (скрыт из OpenAPI)."
        + legacy_integration_path("aitu-redirect/mode/{mode}")
    ),
)
@router.post("/aitu-redirect/mode/{mode}", include_in_schema=False)
async def aitu_redirect(
    request: Request,
    service: AituRedirectServiceDep,
    mode: str,
) -> Response:
    params = dict(request.query_params)
    if mode == "approve":
        try:
            result = await service.handle_approve({k: str(v) for k, v in params.items()})
        except SigningDatabaseError as exc:
            return HTMLResponse(f"<p>DB error: {get_error_message(exc)}</p>", status_code=500)
        if result.get("ok"):
            return HTMLResponse(
                f"<html><body><p>Подпись принята. state={result.get('state')}</p></body></html>"
            )
        return HTMLResponse(
            f"<html><body><p>Ошибка: {result.get('error')}</p>"
            f"<p>state={result.get('state')}</p></body></html>",
            status_code=400,
        )
    return PlainTextResponse("0")


def _parse_legacy_bool_param(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    if value == "":
        return True
    return value.lower() not in ("false", "0", "no")


@router.get(
    "/download-ds",
    summary="downloadDsAction — PDF доп. соглашения",
    description=(
        "Unsigned: office/myspace docx → MyNCA PDF.\n"
        "Signed: `PARTNER_API_URL/get_signed_file/{ds_id}/DS/SIGNED/`.\n"
        "**Query:** `uuid`, `for_view`, `is_base64`."
        + legacy_integration_path("download-ds")
    ),
)
async def download_ds(
    service: SigningDownloadServiceDep,
    uuid: str = Query(""),
    for_view: str | None = Query(None),
    is_base64: str | None = Query(None),
) -> Response:
    return await _download_response(
        service.download_ds(
            uuid,
            for_view=_parse_legacy_bool_param(for_view, default=True),
            is_base64=_parse_legacy_bool_param(is_base64, default=False),
        )
    )


@router.get(
    "/download-agreement",
    summary="downloadAgreementAction — PDF договора",
    description=(
        "Unsigned: office contract report → MyNCA PDF.\n"
        "Signed: partner API `AGREEMENT/SIGNED`.\n"
        "**Query:** `uuid`, `for_view`, `is_base64`."
        + legacy_integration_path("download-agreement")
    ),
)
async def download_agreement(
    service: SigningDownloadServiceDep,
    uuid: str = Query(""),
    for_view: str | None = Query("true"),
    is_base64: str | None = Query(None),
) -> Response:
    return await _download_response(
        service.download_agreement(
            uuid,
            for_view=_parse_legacy_bool_param(for_view, default=True),
            is_base64=_parse_legacy_bool_param(is_base64, default=False),
        )
    )


async def _read_json_object(request: Request) -> dict[str, object] | JSONResponse:
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"status": False, "error": "Невалидный JSON в callback"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"status": False, "error": "Невалидный JSON в callback"}, status_code=400)
    return body


async def _mynca_callback(handler: Awaitable[dict[str, object]]) -> JSONResponse:
    try:
        payload = await handler
        return JSONResponse(payload)
    except SigningDatabaseError as exc:
        return JSONResponse({"status": False, "error": get_error_message(exc)}, status_code=500)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"status": False, "error": get_error_message(exc)}, status_code=500)


@router.post(
    "/callbacks/client-sign",
    summary="MyNCA back_url — клиентская подпись ДС / договора / ОТБАСЫ",
    description=(
        "Вызывает **MyNCA**, не UI. **Auth:** нет.\n\n"
        "`status=SUCCESS` + `meta_data.type_code` (`CLIENT_SIGN` / `CLIENT_DS_SIGN` / "
        "`OTBASY_STATEMENT_SIGN`) → `client.insert_sign_general` + `client.sign_tab__modify`.\n"
        "Другой `status` — HTTP 200 `{\"status\": true}` без записи (как PHP).\n\n"
        "**Legacy:** `POST /client-sign/callback` (`ClientSignController::callbackAction`). "
        "Nginx: проксировать этот path сюда, пока PHP `sign/create` шлёт office `back_url`."
    ),
    openapi_extra=CLIENT_SIGN_BODY,
    responses=MYNCA_CALLBACK_RESPONSES,
)
async def mynca_callback_client_sign(
    request: Request,
    service: MyncaCallbackServiceDep,
) -> JSONResponse:
    body = await _read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await _mynca_callback(service.client_sign(body))


@router.post(
    "/callbacks/project-remont",
    summary="MyNCA back_url — проект ремонта (cabinet)",
    description=(
        "Вызывает **MyNCA**. **Auth:** нет. `ext_id` = `project_remont_id`.\n\n"
        "`SUCCESS` + `is_signed` → `landing.cabinet_project_sign__set`. "
        "Ошибка SP → `landing.cabinet_project_error_sign__clear`.\n\n"
        "**Legacy:** `POST /react/cabinet/project-remont-sign-back/`."
    ),
    openapi_extra=PROJECT_REMONT_BODY,
    responses=MYNCA_CALLBACK_RESPONSES,
)
async def mynca_callback_project_remont(
    request: Request,
    service: MyncaCallbackServiceDep,
) -> JSONResponse:
    body = await _read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await _mynca_callback(service.project_remont(body))


@router.post(
    "/callbacks/app",
    summary="MyNCA back_url — акт приёма-передачи",
    description=(
        "Вызывает **MyNCA**. **Auth:** нет. `ext_id` = `remont_id`, обязателен `group_id`.\n\n"
        "ИИН (`landing.check_iin_sign_client`) → документ `APART_PASS_ACT_CL` "
        "(`client_request_upd_doc` + `cabinet_document_sign_id__set`). "
        "`document_url` = публичная страница MyNCA (`MYNCA_SIGN_PAGE_URL`).\n\n"
        "**Legacy:** `POST /react/cabinet/app-sign-back/`."
    ),
    openapi_extra=CABINET_ACT_BODY,
    responses=MYNCA_CALLBACK_RESPONSES,
)
async def mynca_callback_app(
    request: Request,
    service: MyncaCallbackServiceDep,
) -> JSONResponse:
    body = await _read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await _mynca_callback(service.app(body))


@router.post(
    "/callbacks/defect",
    summary="MyNCA back_url — дефектный акт",
    description=(
        "Как `/callbacks/app`, тип документа `CLIENT_DEFECT_ACT`.\n\n"
        "**Legacy:** `POST /react/cabinet/defect-sign-back/`."
    ),
    openapi_extra=CABINET_ACT_BODY,
    responses=MYNCA_CALLBACK_RESPONSES,
)
async def mynca_callback_defect(
    request: Request,
    service: MyncaCallbackServiceDep,
) -> JSONResponse:
    body = await _read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await _mynca_callback(service.defect(body))


@router.post(
    "/third-party-app-sign-back",
    summary="Callback подписи заявления на 3-е лицо",
    description=(
        "**Auth:** нет. Вызывает **sign.smartremont.kz** (не MyNCA JSON): form/query "
        "`id`, `dn_name`, `signed_xml`, `sign_process_id`.\n\n"
        "`check_iin_sign_third_party_app` → PDF из XML → MinIO → `client_request_upd_doc`.\n"
        "Ответ — JSON в `text/plain` (как PHP `echo json_encode`). GET скрыт из схемы."
        + legacy_integration_path("third-party-app-sign-back")
    ),
    openapi_extra=THIRD_PARTY_FORM_BODY,
    responses=THIRD_PARTY_RESPONSES,
)
@router.get("/third-party-app-sign-back", include_in_schema=False)
async def third_party_app_sign_back(
    request: Request,
    service: ThirdPartySignServiceDep,
) -> PlainTextResponse:
    if request.method == "POST":
        form = await request.form()
        params = {k: str(v) for k, v in form.items()}
    else:
        params = {k: str(v) for k, v in request.query_params.items()}
    try:
        payload = await service.handle(params)
        return PlainTextResponse(json.dumps(payload, ensure_ascii=False))
    except SigningDatabaseError as exc:
        payload = {"status": False, "value": None, "error": get_error_message(exc)}
        return PlainTextResponse(json.dumps(payload, ensure_ascii=False), status_code=500)
    except Exception as exc:  # noqa: BLE001
        payload = {"status": False, "value": None, "error": get_error_message(exc)}
        return PlainTextResponse(json.dumps(payload, ensure_ascii=False), status_code=400)
