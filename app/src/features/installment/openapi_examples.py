"""OpenAPI / Swagger examples for installment FF endpoints."""

CREATE_APPLICATION_REQUEST = {
    "client_request_id": 2916069,
    "provider_code": "FF",
    "iin": "891026301046",
    "mobile_phone": "+77066078118",
    "product_id": "SR_MOCK_FACT_12",
    "loan_type": "installment",
    "principal": 1500000,
    "period": 12,
    "created_by": 42,
}

CREATE_APPLICATION_RESPONSE = {
    "id": 1,
    "uuid": "fc58a802-ce40-4c8b-9cff-9f11930e1702",
    "reference_id": "1",
    "status": "IN_PROGRESS",
    "redirect_url": "https://loan-cash-superapp.example/goods-loan?uuid=fc58a802-ce40-4c8b-9cff-9f11930e1702",
    "provider_code": "FF",
}

FF_PRODUCTS_RESPONSE = {
    "partner_id": "SR_MOCK_PARTNER",
    "name": "Smart Remont",
    "products": [
        {
            "product_id": "SR_MOCK_FACT_12",
            "repayment_method": "INSTALMENT",
            "repayment": [
                {"min": 200000, "max": 8000000, "periods": [12, 24, 36]},
            ],
        },
    ],
}

APPLICATION_RESPONSE = {
    "id": 1,
    "client_request_id": 2916069,
    "provider_code": "FF",
    "uuid": "fc58a802-ce40-4c8b-9cff-9f11930e1702",
    "reference_id": "1",
    "product_id": "SR_MOCK_FACT_12",
    "loan_type": "installment",
    "principal": 1500000,
    "period": 12,
    "status": "APPROVED",
    "approved_params": {
        "principal": 1500000,
        "period": 12,
        "interest_rate": 0,
        "monthly_payment": 125000,
    },
    "redirect_url": "https://loan-cash-superapp.example/goods-loan?uuid=fc58a802-ce40-4c8b-9cff-9f11930e1702",
    "created_by": 42,
    "created_at": "2026-06-17T10:00:00+00:00",
    "updated_at": "2026-06-17T10:05:00+00:00",
}

WEBHOOK_APPROVED = {
    "uuid": "fc58a802-ce40-4c8b-9cff-9f11930e1702",
    "reference_id": "1",
    "status": "APPROVED",
    "loan_type": "installment",
    "product": "SR_MOCK_FACT_12",
    "approved_params": {
        "principal": 1500000,
        "period": 12,
        "interest_rate": 0,
        "effective_rate": 0,
        "monthly_payment": 125000,
    },
    "alternative_reason": "",
}

WEBHOOK_REJECTED = {
    "uuid": "fc58a802-ce40-4c8b-9cff-9f11930e1702",
    "reference_id": "1",
    "status": "REJECTED",
    "loan_type": "installment",
    "product": "SR_MOCK_FACT_12",
    "approved_params": {
        "principal": 1500000,
        "period": 12,
        "interest_rate": 0,
        "monthly_payment": 0,
    },
    "alternative_reason": "Скоринг отказал",
}

WEBHOOK_ISSUED = {
    "uuid": "fc58a802-ce40-4c8b-9cff-9f11930e1702",
    "reference_id": "1",
    "status": "ISSUED",
    "loan_type": "installment",
    "product": "SR_MOCK_FACT_12",
    "approved_params": {
        "principal": 1500000,
        "period": 12,
        "interest_rate": 0,
        "monthly_payment": 125000,
    },
}

WEBHOOK_ACK_RESPONSE = {"ok": True}

# Route-level OpenAPI fragments (Swagger shows these in Try it out / Examples dropdown)
CREATE_APPLICATION_BODY = {
    "installment": {
        "summary": "Рассрочка на ремонт",
        "description": "ИИН и телефон заёмщика — в теле запроса, могут отличаться от владельца client_request.",
        "value": CREATE_APPLICATION_REQUEST,
    },
}

CREATE_APPLICATION_RESPONSES = {
    201: {
        "description": "Заявка создана, клиент переходит по redirect_url",
        "content": {
            "application/json": {
                "examples": {
                    "in_progress": {
                        "summary": "Отправлено в FF",
                        "value": CREATE_APPLICATION_RESPONSE,
                    },
                },
            },
        },
    },
}

FF_PRODUCTS_RESPONSES = {
    200: {
        "description": "Каталог продуктов партнёра из FF get-partner-info",
        "content": {
            "application/json": {
                "examples": {
                    "mock": {
                        "summary": "Mock seed (SR_MOCK_*)",
                        "value": FF_PRODUCTS_RESPONSE,
                    },
                },
            },
        },
    },
}

APPLICATION_RESPONSES = {
    200: {
        "description": "Текущее состояние заявки в БД",
        "content": {
            "application/json": {
                "examples": {
                    "approved": {
                        "summary": "Одобрено (после webhook)",
                        "value": APPLICATION_RESPONSE,
                    },
                },
            },
        },
    },
}

WEBHOOK_ACK_RESPONSES = {
    200: {
        "description": "Webhook принят (идемпотентно при повторе)",
        "content": {
            "application/json": {
                "examples": {
                    "ok": {"value": WEBHOOK_ACK_RESPONSE},
                },
            },
        },
    },
}
