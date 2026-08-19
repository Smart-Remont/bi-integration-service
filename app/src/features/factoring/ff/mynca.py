from typing import Any

import httpx
from fastapi import HTTPException, status
from loguru import logger


class MyncaClientError(Exception):
    def __init__(self, detail: str, status_code: int = 502) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class MyncaClient:
    """HTTP client for nca.smartremont.kz — same API as constructor MyNcaClient."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token.strip()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "SmartRemont-integrations-sr-factoring/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def require_configured(self) -> None:
        if not self.base_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MYNCA_BASE_URL is not configured.",
            )
        if not self.token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MYNCA_TOKEN is not configured.",
            )

    async def docx_to_pdf(self, docx_bytes: bytes) -> bytes:
        payload = {"docx": _b64(docx_bytes), "is_file": False}
        body = await self._request_json("POST", "/document/docx-to-pdf", json=payload)
        pdf_b64 = _nested_str(body, "pdf") or _nested_str(body, "data", "pdf")
        if not pdf_b64:
            raise MyncaClientError("MyNCA docx-to-pdf returned empty PDF.")
        try:
            import base64

            return base64.b64decode(pdf_b64)
        except Exception as exc:  # noqa: BLE001
            raise MyncaClientError("MyNCA docx-to-pdf returned invalid PDF.") from exc

    async def sign_create(
        self,
        *,
        file_name: str,
        pdf_bytes: bytes,
        ext_id: int,
        meta_data: dict[str, Any],
        back_url: str,
        return_url: str,
        exp_minutes: int = 60,
    ) -> tuple[str, str]:
        import base64

        payload = {
            "file_name": file_name,
            "file_content": base64.b64encode(pdf_bytes).decode("ascii"),
            "ext_id": ext_id,
            "meta_data": meta_data,
            "back_url": back_url,
            "return_url": return_url,
            "exp_minutes": exp_minutes,
        }
        body = await self._request_json("POST", "/sign/create", json=payload)
        data = _unwrap_data(body)
        sign_url = data.get("sign_url")
        sign_process_id = data.get("sign_process_id")
        if not isinstance(sign_url, str) or not sign_url:
            raise MyncaClientError("MyNCA sign/create did not return sign_url.")
        if not isinstance(sign_process_id, str) or not sign_process_id:
            raise MyncaClientError("MyNCA sign/create did not return sign_process_id.")
        return sign_url, sign_process_id

    async def sign_status(self, sign_process_id: str) -> str:
        body = await self._request_json(
            "GET",
            f"/sign/{sign_process_id}/status",
        )
        data = _unwrap_data(body)
        raw = data.get("status")
        if isinstance(raw, str) and raw.strip():
            return raw.strip().upper()
        return ""

    async def sign_download_pdf(self, sign_process_id: str) -> bytes:
        return await self._request_bytes("GET", f"/sign/{sign_process_id}/download")

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._request(method, path, json=json)
        try:
            body = response.json()
        except ValueError as exc:
            raise MyncaClientError(
                f"MyNCA {path} returned non-JSON (HTTP {response.status_code})."
            ) from exc
        if not isinstance(body, dict):
            raise MyncaClientError(f"MyNCA {path} returned unexpected JSON.")
        if response.status_code >= 400:
            message = (
                _nested_str(body, "message")
                or _nested_str(body, "data", "message")
                or f"MyNCA HTTP {response.status_code}"
            )
            raise MyncaClientError(message, status_code=502)
        return body

    async def _request_bytes(self, method: str, path: str) -> bytes:
        response = await self._request(method, path, json=None)
        if response.status_code >= 400:
            raise MyncaClientError(
                f"MyNCA {path} failed (HTTP {response.status_code})."
            )
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            body = response.json()
            pdf_b64 = _nested_str(body, "pdf") or _nested_str(body, "data", "pdf")
            if pdf_b64:
                import base64

                return base64.b64decode(pdf_b64)
            raise MyncaClientError(f"MyNCA {path} JSON response has no PDF.")
        if not response.content:
            raise MyncaClientError(f"MyNCA {path} returned empty body.")
        return response.content

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None,
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        timeout = httpx.Timeout(timeout=60.0, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json,
                )
        except httpx.RequestError as exc:
            logger.error("MyNCA transport error | url={url} error={error}", url=url, error=exc)
            raise MyncaClientError(f"MyNCA request failed: {exc}") from exc
        logger.info(
            "MyNCA HTTP | method={method} path={path} status={status}",
            method=method,
            path=path,
            status=response.status_code,
        )
        return response


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _unwrap_data(body: dict[str, Any]) -> dict[str, Any]:
    data = body.get("data")
    if isinstance(data, dict):
        nested = data.get("data")
        if isinstance(nested, dict):
            return nested
        return data
    return body


def _nested_str(payload: dict[str, Any], *keys: str) -> str | None:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if isinstance(current, str) and current.strip():
        return current
    return None
