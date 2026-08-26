from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import ConfigDict, Field
from src.schema import BaseSchema

from .openapi_examples import (
    APPLICATION_RESPONSE,
    CREATE_APPLICATION_REQUEST,
    CREATE_APPLICATION_RESPONSE,
    WEBHOOK_ACK_RESPONSE,
)


class PrintFormItem(BaseSchema):
    name: str = Field(description="application | notification (уточнить у банка)")
    url: str = Field(description="URL уже подписанного документа")


class CreditGoodItem(BaseSchema):
    cost: Decimal | None = None
    good_identifier: str | None = None
    quantity: int | None = None
    brand: str | None = None
    model: str | None = None
    category: str | None = None


class PrepareFactoringDocumentsRequest(BaseSchema):
    client_request_id: int = Field(examples=[2916069])
    iin: str = Field(examples=["891026301046"])
    mobile_phone: str = Field(examples=["+77066078118"])
    principal: Decimal = Field(examples=[119890])
    period: int = Field(examples=[12])
    created_by: int = Field(examples=[42])
    client_fio: str | None = Field(default=None, description="ФИО клиента для печатных форм")
    branch_code: str = Field(default="200000")
    product_id: str | None = None
    prepayment_amount: Decimal | None = None
    interest_rate: Decimal | None = None
    credit_goods: list[CreditGoodItem] | None = None
    is_knox: bool = False


class FactoringSignDocument(BaseSchema):
    name: str
    title: str
    sign_url: str | None = None
    signed: bool = False
    url: str | None = None


class PrepareFactoringDocumentsResponse(BaseSchema):
    id: int
    credit_contract: str
    status: str
    provider_code: str
    documents: list[FactoringSignDocument]


class SubmitFactoringApplicationRequest(BaseSchema):
    is_knox: bool = False


class CreateFactoringApplicationRequest(BaseSchema):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_alias=True,
        validate_by_name=True,
        json_schema_extra={"examples": [CREATE_APPLICATION_REQUEST]},
    )

    client_request_id: int = Field(examples=[2916069])
    iin: str = Field(examples=["891026301046"])
    mobile_phone: str = Field(examples=["+77066078118"])
    principal: Decimal = Field(examples=[119890])
    period: int = Field(examples=[12])
    created_by: int = Field(examples=[42])
    print_forms: list[PrintFormItem] = Field(min_length=1)
    credit_contract: str | None = Field(
        default=None,
        description="FCT{YY}-{BRANCH}-{SEQ}. Если не передан — сгенерируется.",
    )
    branch_code: str = Field(
        default="200000",
        description="Код филиала банка (Алматы=200000). См. docs Коды филиалов.",
    )
    product_id: str | None = Field(
        default=None,
        description="По умолчанию config.default_product_id провайдера",
    )
    prepayment_amount: Decimal | None = None
    interest_rate: Decimal | None = None
    credit_goods: list[CreditGoodItem] | None = None
    is_knox: bool = False


class CreateFactoringApplicationResponse(BaseSchema):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_alias=True,
        validate_by_name=True,
        json_schema_extra={"examples": [CREATE_APPLICATION_RESPONSE]},
    )

    id: int
    uuid: str
    reference_id: str
    credit_contract: str
    status: str
    redirect_url: str | None = None
    provider_code: str


class FactoringApplicationResponse(BaseSchema):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_alias=True,
        validate_by_name=True,
        json_schema_extra={"examples": [APPLICATION_RESPONSE]},
    )

    id: int
    client_request_id: int
    provider_code: str
    uuid: str | None = None
    reference_id: str | None = None
    credit_contract: str
    branch_code: str | None = None
    product_id: str | None = None
    partner: str | None = None
    channel: str | None = None
    principal: Decimal | None = None
    period: int | None = None
    prepayment_amount: Decimal | None = None
    interest_rate: Decimal | None = None
    status: str
    approved_params: dict[str, Any] | None = None
    redirect_url: str | None = None
    print_forms: list[Any] | None = None
    credit_goods: list[Any] | None = None
    request_payload: dict[str, Any] | None = None
    issued_at: datetime | None = None
    client_request_credit_detail_id: int | None = None
    created_by: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FactoringApplicationListResponse(BaseSchema):
    items: list[FactoringApplicationResponse]
    total: int


class SendCessionRequest(BaseSchema):
    issue_date: str | None = Field(
        default=None,
        description="YYYY-MM-DD. По умолчанию — сегодня. Собирает ISSUED/REVERSED выдачи за эту дату.",
        examples=["2026-08-26"],
    )
    dry_run: bool = Field(
        default=False,
        description="Если true — считает сумму и список заявок, но не подписывает и не отправляет в банк.",
    )


class CessionApplicationItem(BaseSchema):
    id: int
    uuid: str | None = None
    credit_contract: str
    principal: Decimal
    status: str


class CessionBatchResult(BaseSchema):
    company_id: int | None = None
    partner: str | None = Field(
        default=None,
        description="Партнёр банка для этого юрлица. null — юрлицо не смаппено на partner, батч не отправлен.",
    )
    contract_number: str | None = None
    payment_amount: Decimal
    applications: list[CessionApplicationItem]
    sent: bool
    bank_message: str | None = None
    sign_process_id: str | None = Field(
        default=None,
        description="MyNCA sign_process_id (cms/sign-save) для подписи договора цессии.",
    )
    sign_group_id: str | None = Field(
        default=None,
        description="MyNCA group_id (cms/sign-save) — та же группа, что и sign_process_id.",
    )


class SendCessionResponse(BaseSchema):
    issue_date: str
    batches: list[CessionBatchResult]


class FactoringWebhookPayload(BaseSchema):
    model_config = ConfigDict(extra="allow")

    uuid: str | None = None
    reference_id: str | None = None
    status: str | None = None
    approved_params: dict[str, Any] | None = None


class WebhookAckResponse(BaseSchema):
    model_config = ConfigDict(
        json_schema_extra={"examples": [WEBHOOK_ACK_RESPONSE]},
    )

    ok: bool = True
