from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import ConfigDict, Field
from src.schema import BaseSchema

from .openapi_examples import (
    APPLICATION_RESPONSE,
    CREATE_APPLICATION_REQUEST,
    CREATE_APPLICATION_RESPONSE,
    FF_PRODUCTS_RESPONSE,
    WEBHOOK_ACK_RESPONSE,
    WEBHOOK_APPROVED,
    WEBHOOK_ISSUED,
    WEBHOOK_REJECTED,
)


class FFPrincipalLimits(BaseSchema):
    min: Decimal
    max: Decimal


class FFRepaymentCondition(BaseSchema):
    periods: list[int]
    principal_limits: FFPrincipalLimits


class FFProduct(BaseSchema):
    product_id: str
    repayment_method: str
    repayment: list[FFRepaymentCondition]


class FFProductsResponse(BaseSchema):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_alias=True,
        validate_by_name=True,
        json_schema_extra={"examples": [FF_PRODUCTS_RESPONSE]},
    )

    partner_id: str
    name: str
    products: list[FFProduct]


class InstallmentApplicationListResponse(BaseSchema):
    items: list["InstallmentApplicationResponse"]
    total: int


class CreateInstallmentApplicationRequest(BaseSchema):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_alias=True,
        validate_by_name=True,
        json_schema_extra={"examples": [CREATE_APPLICATION_REQUEST]},
    )

    client_request_id: int = Field(
        description="ID ремонта в SR (client_request_tab). ИИН/телефон — отдельно.",
        examples=[2916069],
    )
    provider_code: Literal["FF"] = Field(description="Провайдер рассрочки", examples=["FF"])
    iin: str = Field(
        description="ИИН заёмщика (12 цифр). Может отличаться от владельца заявки на ремонт.",
        examples=["891026301046"],
    )
    mobile_phone: str = Field(
        description="Телефон заёмщика в формате +7...",
        examples=["+77066078118"],
    )
    product_id: str = Field(
        description="product_id из GET /ff/products",
        examples=["SR_MOCK_FACT_12"],
    )
    repayment_method: str = Field(
        description="repayment_method из продукта FF: ANNUITY | EQUAL_INSTALMENTS | INSTALLMENT",
        examples=["INSTALLMENT"],
    )
    loan_type: Literal["installment", "credit"] = Field(
        default="installment",
        description="installment — рассрочка 0%, credit — кредит",
        examples=["installment"],
    )
    principal: Decimal = Field(description="Сумма займа", examples=[1500000])
    period: int = Field(description="Срок, месяцев", examples=[12])
    created_by: int = Field(description="ID пользователя (hunter)", examples=[42])


class CreateInstallmentApplicationResponse(BaseSchema):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_alias=True,
        validate_by_name=True,
        json_schema_extra={"examples": [CREATE_APPLICATION_RESPONSE]},
    )

    id: int
    uuid: str
    reference_id: str
    status: str
    redirect_url: str | None = None
    provider_code: str


class InstallmentApplicationResponse(BaseSchema):
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
    product_id: str | None = None
    loan_type: str | None = None
    principal: Decimal | None = None
    period: int | None = None
    status: str
    approved_params: dict[str, Any] | None = None
    redirect_url: str | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime


class FFWebhookPayload(BaseSchema):
    model_config = ConfigDict(
        extra="allow",
        from_attributes=True,
        validate_by_alias=True,
        validate_by_name=True,
        json_schema_extra={
            "examples": [WEBHOOK_APPROVED, WEBHOOK_REJECTED, WEBHOOK_ISSUED],
        },
    )

    status: str = Field(
        description="REJECTED | APPROVED | ALTERNATIVE | ISSUED",
        examples=["APPROVED"],
    )
    uuid: str | None = Field(default=None, examples=["fc58a802-ce40-4c8b-9cff-9f11930e1702"])
    reference_id: str | None = Field(default=None, description="Наш id заявки", examples=["1"])
    lead_id: str | None = None
    approved_params: dict[str, Any] | None = None
    loan_type: str | None = Field(default=None, examples=["installment"])
    product: str | None = Field(default=None, examples=["SR_MOCK_FACT_12"])
    redirect_url: str | None = None
    alternative_reason: str | None = Field(default=None, examples=[""])


class WebhookAckResponse(BaseSchema):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_alias=True,
        validate_by_name=True,
        json_schema_extra={"examples": [WEBHOOK_ACK_RESPONSE]},
    )

    ok: bool = Field(examples=[True])
