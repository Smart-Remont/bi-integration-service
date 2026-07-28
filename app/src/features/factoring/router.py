from typing import Annotated

from fastapi import APIRouter, Body, Path, Request, status
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
    WebhookAckResponse,
)

router = APIRouter(prefix=api_prefix_config.v1.factoring_ff, tags=["Factoring FF"])


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
        "Создаёт запись в `factoring_application_tab`, вызывает банк "
        "`apply-lead-factoring`. Нужны ИИН, телефон и подписанные `print_forms`."
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
        Path(description="ID в factoring_application_tab", examples=[1]),
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
