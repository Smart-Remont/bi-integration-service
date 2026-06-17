from typing import Annotated

from fastapi import APIRouter, Body, Path, Request, status
from src.routers import api_prefix_config

from .deps import FFServiceDep
from .openapi_examples import (
    APPLICATION_RESPONSES,
    CREATE_APPLICATION_BODY,
    CREATE_APPLICATION_RESPONSES,
    FF_PRODUCTS_RESPONSES,
    WEBHOOK_ACK_RESPONSES,
    WEBHOOK_APPROVED,
    WEBHOOK_ISSUED,
    WEBHOOK_REJECTED,
)
from .schemas import (
    CreateInstallmentApplicationRequest,
    CreateInstallmentApplicationResponse,
    FFWebhookPayload,
    FFProductsResponse,
    InstallmentApplicationResponse,
    WebhookAckResponse,
)

router = APIRouter(prefix=api_prefix_config.v1.installment_ff, tags=["Installment FF"])


@router.get(
    "/products",
    response_model=FFProductsResponse,
    summary="Условия продуктов FF",
    description=(
        "Прокси к Freedom Finance `get-partner-info`. "
        "Возвращает доступные `product_id`, диапазоны сумм и сроки для UI."
    ),
    responses=FF_PRODUCTS_RESPONSES,
)
async def get_ff_products(ff_service: FFServiceDep) -> FFProductsResponse:
    return await ff_service.get_products()


@router.post(
    "/applications",
    response_model=CreateInstallmentApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заявку на рассрочку (FF)",
    description=(
        "Создаёт запись в БД, вызывает FF `goods-loan-lead`. "
        "**ИИН и телефон** передаются в теле — заёмщик может отличаться от клиента в `client_request_id`."
    ),
    responses=CREATE_APPLICATION_RESPONSES,
)
async def create_application(
    request: Annotated[
        CreateInstallmentApplicationRequest,
        Body(openapi_examples=CREATE_APPLICATION_BODY),
    ],
    ff_service: FFServiceDep,
) -> CreateInstallmentApplicationResponse:
    return await ff_service.create_application(request)


@router.get(
    "/applications/{application_id}",
    response_model=InstallmentApplicationResponse,
    summary="Статус заявки",
    description="Локальное состояние из `installment_application_tab` (после webhook/poll).",
    responses=APPLICATION_RESPONSES,
)
async def get_application(
    application_id: Annotated[
        int,
        Path(description="ID в installment_application_tab", examples=[1]),
    ],
    ff_service: FFServiceDep,
) -> InstallmentApplicationResponse:
    return await ff_service.get_application_by_id(application_id)


@router.post(
    "/applications/{application_id}/poll",
    response_model=InstallmentApplicationResponse,
    summary="Опрос статуса в FF",
    description="Вызывает FF `goods-application-info/{uuid}` и обновляет заявку в БД.",
    responses=APPLICATION_RESPONSES,
)
async def poll_application(
    application_id: Annotated[
        int,
        Path(description="ID в installment_application_tab", examples=[1]),
    ],
    ff_service: FFServiceDep,
) -> InstallmentApplicationResponse:
    return await ff_service.poll_application(application_id)


@router.post(
    "/webhook",
    response_model=WebhookAckResponse,
    summary="Webhook от Freedom Finance",
    description=(
        "Входящий hook от банка. Basic Auth — если настроены `webhook_username` / `webhook_password` у провайдера FF. "
        "В Swagger выберите пример: approved / rejected / issued."
    ),
    responses=WEBHOOK_ACK_RESPONSES,
)
async def webhook_ff(
    request: Request,
    body: Annotated[
        FFWebhookPayload,
        Body(
            openapi_examples={
                "approved": {
                    "summary": "APPROVED — скоринг одобрил",
                    "value": WEBHOOK_APPROVED,
                },
                "rejected": {
                    "summary": "REJECTED — отказ",
                    "value": WEBHOOK_REJECTED,
                },
                "issued": {
                    "summary": "ISSUED — заём выдан",
                    "value": WEBHOOK_ISSUED,
                },
            },
        ),
    ],
    ff_service: FFServiceDep,
) -> WebhookAckResponse:
    payload = body.model_dump()
    if body.__pydantic_extra__:
        payload.update(body.__pydantic_extra__)
    authorization_header = request.headers.get("Authorization")
    return await ff_service.handle_webhook(payload, authorization_header=authorization_header)
