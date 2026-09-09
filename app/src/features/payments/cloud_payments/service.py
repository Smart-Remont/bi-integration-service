from __future__ import annotations

import json
from html import unescape
from typing import Any
from urllib.parse import parse_qs

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from src.service import BaseService

from ..errors import PaymentsDatabaseError
from .repo import CloudPaymentsRepository


class CloudPaymentsService(BaseService):
    def __init__(self, repository: CloudPaymentsRepository) -> None:
        self.repository = repository

    async def handle(self, mode: str, request: Request) -> JSONResponse:
        payload = await self._parse_body(request) or {}

        client_request_id_hash = self._extract_request_hash(payload)
        client_request_payment_id_hash = str(payload.get("InvoiceId") or "")
        payment_amount = int(payload.get("Amount") or 0)
        cp_transaction_id = str(payload.get("TransactionId") or "")
        cp_response = CloudPaymentsRepository.cp_response_json(payload)

        logger.info(
            "cloudpayments mode={mode} invoice={invoice}",
            mode=mode,
            invoice=client_request_payment_id_hash,
        )

        try:
            code = await self.repository.cloud_payments_pay(
                mode,
                client_request_id_hash,
                client_request_payment_id_hash,
                payment_amount,
                cp_response,
                cp_transaction_id,
            )
        except PaymentsDatabaseError as exc:
            logger.warning("cloudpayments SP error: {error}", error=exc.message)
            return JSONResponse({"code": 13})

        if mode == "check":
            return JSONResponse({"code": code})

        if mode in ("pay", "fail"):
            if code is None:
                return JSONResponse({"code": 13})
            if mode == "pay":
                row = await self.repository.payment_client_request_get(
                    client_request_payment_id_hash,
                    client_request_id_hash,
                )
                if row:
                    logger.info(
                        "cloudpayments pay amount={amount} payment_amount={payment_amount}",
                        amount=payment_amount,
                        payment_amount=row.get("payment_amount"),
                    )
            return JSONResponse({"code": code})

        return JSONResponse({"code": 13})

    @staticmethod
    async def _parse_body(request: Request) -> dict[str, Any] | None:
        raw = await request.body()
        if not raw:
            return {}
        text = unescape(raw.decode(errors="replace"))
        flat = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(text, keep_blank_values=True).items()}
        return flat

    @staticmethod
    def _extract_request_hash(payload: dict[str, Any]) -> str:
        data_raw = payload.get("Data")
        if not data_raw:
            return ""
        try:
            parsed = json.loads(data_raw)
        except json.JSONDecodeError:
            return str(data_raw)
        if isinstance(parsed, dict):
            return str(parsed.get("hash") or "")
        return str(parsed)
