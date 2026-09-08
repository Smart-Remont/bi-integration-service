from typing import Any

import httpx

from .xml_helpers import parse_xml_response


class ForteClientError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ForteClient:
    async def post_xml(self, url: str, xml_body: str) -> list[dict[str, Any]]:
        if not url:
            raise ForteClientError("Forte URL is not configured (FORTE_URL setting or FORTE_URL env)")

        timeout = httpx.Timeout(timeout=10.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            try:
                response = await client.post(url, content=xml_body.encode("utf-8"))
            except httpx.RequestError as exc:
                raise ForteClientError(str(exc)) from exc

        if response.status_code >= 400:
            raise ForteClientError(f"Forte HTTP {response.status_code}: {response.text[:300]}")

        try:
            return parse_xml_response(response.text, "Response")
        except Exception as exc:
            raise ForteClientError(f"Invalid Forte XML: {exc}") from exc
