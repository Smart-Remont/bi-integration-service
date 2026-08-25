from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, Request, status
from fastapi.responses import Response
from src.routers.config import api_prefix_config

from .auth import FactoringBasicAuthDep
from .deps import FactoringServiceDep
from .openapi_examples import (
    APPLICATION_RESPONSES,
    CREATE_APPLICATION_BODY,
    CREATE_APPLICATION_RESPONSES,
    WEBHOOK_ACK_RESPONSES,
    WEBHOOK_APPROVED,
    WEBHOOK_ISSUED,
    WEBHOOK_REJECTED,
)
from .schemas import (
    CreateFactoringApplicationRequest,
    CreateFactoringApplicationResponse,
    FactoringApplicationListResponse,
    FactoringApplicationResponse,
    FactoringWebhookPayload,
    PrepareFactoringDocumentsRequest,
    PrepareFactoringDocumentsResponse,
    SubmitFactoringApplicationRequest,
    WebhookAckResponse,
)

router = APIRouter(prefix=api_prefix_config.v1.factoring_ff, tags=["Factoring (Freedom Finance)"])


@router.get(
    "/applications",
    response_model=FactoringApplicationListResponse,
    summary="Список факторинговых заявок по client_request_id",
)
async def list_applications(
    _: FactoringBasicAuthDep,
    client_request_id: int,
    service: FactoringServiceDep,
) -> FactoringApplicationListResponse:
    items = await service.get_applications_by_client_request(client_request_id)
    return FactoringApplicationListResponse(items=items, total=len(items))


@router.post(
    "/applications",
    response_model=CreateFactoringApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заявку на факторинг (FFC2)",
    description=(
        "Создаёт запись в `installment_application_tab` (`product_type = FACTORING`), "
        "вызывает банк `apply-lead-factoring`. Нужны ИИН, телефон и подписанные `print_forms`."
    ),
    responses=CREATE_APPLICATION_RESPONSES,
)
async def create_application(
    _: FactoringBasicAuthDep,
    request: Annotated[
        CreateFactoringApplicationRequest,
        Body(openapi_examples=CREATE_APPLICATION_BODY),
    ],
    service: FactoringServiceDep,
) -> CreateFactoringApplicationResponse:
    return await service.create_application(request)


@router.post(
    "/applications/prepare",
    response_model=PrepareFactoringDocumentsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Подготовить печатные формы и отправить клиенту на ЭЦП",
)
async def prepare_documents(
    _: FactoringBasicAuthDep,
    request: PrepareFactoringDocumentsRequest,
    service: FactoringServiceDep,
) -> PrepareFactoringDocumentsResponse:
    return await service.prepare_documents(request)


@router.post(
    "/applications/{application_id}/refresh-sign",
    response_model=PrepareFactoringDocumentsResponse,
    summary="Проверить статусы ЭЦП печатных форм",
)
async def refresh_sign_status(
    _: FactoringBasicAuthDep,
    application_id: Annotated[int, Path(examples=[1])],
    service: FactoringServiceDep,
) -> PrepareFactoringDocumentsResponse:
    return await service.refresh_sign_status(application_id)


@router.post(
    "/applications/{application_id}/submit",
    response_model=CreateFactoringApplicationResponse,
    summary="Отправить подписанную заявку в банк",
    responses=CREATE_APPLICATION_RESPONSES,
)
async def submit_application(
    _: FactoringBasicAuthDep,
    application_id: Annotated[int, Path(examples=[1])],
    request: SubmitFactoringApplicationRequest,
    service: FactoringServiceDep,
) -> CreateFactoringApplicationResponse:
    return await service.submit_application(application_id, request)


@router.get(
    "/print-forms/{application_id}/{name}",
    summary="Публичный PDF печатной формы (для банка после ЭЦП)",
)
async def download_print_form(
    application_id: int,
    name: str,
    service: FactoringServiceDep,
    t: Annotated[str, Query(description="file_token")],
) -> Response:
    pdf = await service.get_print_form_file(application_id, name, t)
    return Response(content=pdf, media_type="application/pdf")


@router.post(
    "/sign-callback",
    response_model=WebhookAckResponse,
    summary="Callback MyNCA после подписи (no-op, статус проверяем poll)",
)
async def sign_callback() -> WebhookAckResponse:
    return WebhookAckResponse(ok=True)


@router.get(
    "/applications/{application_id}",
    response_model=FactoringApplicationResponse,
    summary="Статус факторинговой заявки",
    responses=APPLICATION_RESPONSES,
)
async def get_application(
    _: FactoringBasicAuthDep,
    application_id: Annotated[
        int,
        Path(description="ID в installment_application_tab (product_type = FACTORING)", examples=[1]),
    ],
    service: FactoringServiceDep,
) -> FactoringApplicationResponse:
    return await service.get_application_by_id(application_id)


@router.post(
    "/webhook",
    response_model=WebhookAckResponse,
    summary="Webhook статусов факторинга от Freedom",
    description=(
        "Входящий hook. Basic Auth — если заданы webhook_username/password у провайдера "
        "`FF_FACTORING`."
    ),
    responses=WEBHOOK_ACK_RESPONSES,
)
async def webhook_factoring(
    request: Request,
    body: Annotated[
        FactoringWebhookPayload,
        Body(
            openapi_examples={
                "approved": {"summary": "APPROVED", "value": WEBHOOK_APPROVED},
                "rejected": {"summary": "REJECTED", "value": WEBHOOK_REJECTED},
                "issued": {"summary": "ISSUED", "value": WEBHOOK_ISSUED},
            },
        ),
    ],
    service: FactoringServiceDep,
) -> WebhookAckResponse:
    payload = body.model_dump()
    if body.__pydantic_extra__:
        payload.update(body.__pydantic_extra__)
    authorization_header = request.headers.get("Authorization")
    return await service.handle_webhook(payload, authorization_header=authorization_header)
