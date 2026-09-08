from typing import Any

import httpx
from src.config import sberbank_config


class SberbankClientError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SberbankClient:
    """Sberbank.kz payment REST API (legacy ``SberbankController``)."""

    def _base_url(self) -> str:
        if sberbank_config.test_mode:
            return sberbank_config.base_url_test
        return sberbank_config.base_url_prod

    def _credentials(self) -> tuple[str, str]:
        user = sberbank_config.user
        password = (
            sberbank_config.password_test if sberbank_config.test_mode else sberbank_config.password
        )
        if not user or not password:
            raise SberbankClientError("Sberbank credentials are not configured (SBERBANK_*)")
        return user, password

    async def _post(self, operation: str, payload: dict[str, object]) -> dict[str, Any]:
        user, password = self._credentials()
        body = {"userName": user, "password": password, **payload}
        url = f"{self._base_url()}/{operation}.do"
        timeout = httpx.Timeout(timeout=60.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            try:
                response = await client.post(url, data=body)
            except httpx.RequestError as exc:
                raise SberbankClientError(str(exc)) from exc

        try:
            parsed = response.json()
        except ValueError as exc:
            raise SberbankClientError(f"Invalid JSON from Sberbank: {response.text[:200]}") from exc

        if not isinstance(parsed, dict):
            raise SberbankClientError("Unexpected Sberbank response shape")
        return parsed

    async def register(
        self,
        order_number: object,
        amount_kopecks: int,
        return_url: str,
    ) -> dict[str, Any]:
        return await self._post(
            "register",
            {
                "orderNumber": order_number,
                "amount": amount_kopecks,
                "returnUrl": return_url,
            },
        )

    async def get_order_status_extended(
        self,
        order_id: object | None,
        order_number: object | None,
    ) -> dict[str, Any]:
        return await self._post(
            "getOrderStatusExtended",
            {
                "orderId": order_id,
                "orderNumber": order_number,
            },
        )
