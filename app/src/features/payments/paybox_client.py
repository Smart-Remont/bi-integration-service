from typing import Any

import httpx

from .xml_helpers import parse_xml_response


class PayboxClientError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class PayboxClient:
    async def post_form(self, url: str, data: dict[str, Any]) -> list[dict[str, Any]]:
        if not url:
            raise PayboxClientError("Paybox URL is not configured")

        timeout = httpx.Timeout(timeout=10.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            try:
                response = await client.post(url, data=data)
            except httpx.RequestError as exc:
                raise PayboxClientError(str(exc)) from exc

        if response.status_code >= 400:
            raise PayboxClientError(f"Paybox HTTP {response.status_code}: {response.text[:300]}")

        try:
            return parse_xml_response(response.text, "response")
        except Exception as exc:
            raise PayboxClientError(f"Invalid Paybox XML: {exc}") from exc
