from typing import Any
from urllib.parse import urlencode

import httpx
from loguru import logger


class FFClientError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class FFClient:
    async def authenticate(self, base_url: str, username: str, password: str) -> tuple[str, str | None]:
        payload = {
            "username": username,
            "password": password,
        }
        response = await self._request(
            method="POST",
            base_url=base_url,
            path="/ffc-api-auth/",
            json=payload,
        )
        access = response.get("access")
        refresh = response.get("refresh")
        if not isinstance(access, str) or not access:
            raise FFClientError(status_code=502, detail="Freedom Finance did not return access token.")
        if refresh is not None and not isinstance(refresh, str):
            raise FFClientError(status_code=502, detail="Freedom Finance returned invalid refresh token.")
        return access, refresh

    async def get_partner_info(
        self,
        base_url: str,
        access_token: str,
        partner_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            base_url=base_url,
            path="/ffc-api-public/universal/additional/get-partner-info",
            params={"partner-id": partner_id},
            headers={"Authorization": f"JWT {access_token}"},
        )

    async def apply_goods_loan_lead(
        self,
        base_url: str,
        access_token: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            base_url=base_url,
            path="/ffc-api-public/universal/apply/goods-loan-lead",
            json=payload,
            headers={"Authorization": f"JWT {access_token}"},
        )

    async def get_goods_application_info(
        self,
        base_url: str,
        access_token: str,
        uuid: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            base_url=base_url,
            path=f"/ffc-api-public/universal/additional/goods-application-info/{uuid}",
            headers={"Authorization": f"JWT {access_token}"},
        )

    async def _request(
        self,
        method: str,
        base_url: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_url = f"{base_url.rstrip('/')}{path}"
        if params:
            request_url = f"{request_url}?{urlencode(params)}"

        logger.info(
            "FF HTTP request | method={method} url={url} headers={headers} body={body}",
            method=method,
            url=request_url,
            headers=self._mask_headers(headers),
            body=self._mask_json_body(json),
        )

        timeout = httpx.Timeout(timeout=20.0, connect=10.0)
        try:
            async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=path,
                    headers=headers,
                    params=params,
                    json=json,
                )
        except httpx.RequestError as exc:
            logger.error("FF HTTP transport error | url={url} error={error}", url=request_url, error=exc)
            raise FFClientError(
                status_code=502,
                detail=f"Freedom Finance request failed: {exc}",
            ) from exc

        logger.info(
            "FF HTTP response | url={url} status={status} body={body}",
            url=request_url,
            status=response.status_code,
            body=self._truncate_response_body(response),
        )
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if response.is_success:
            if not isinstance(payload, dict):
                raise FFClientError(status_code=502, detail="Freedom Finance returned invalid JSON payload.")
            return payload

        detail: str
        if isinstance(payload, dict):
            message = payload.get("message") or payload.get("detail")
            if isinstance(message, str) and message.strip():
                detail = message
            else:
                detail = "Freedom Finance request failed."
        else:
            detail = f"Freedom Finance request failed with status {response.status_code}."

        logger.warning(
            "FF HTTP error | status={status} detail={detail} raw_body={body}",
            status=response.status_code,
            detail=detail,
            body=self._truncate_response_body(response),
        )
        raise FFClientError(status_code=response.status_code, detail=detail)

    @staticmethod
    def _mask_headers(headers: dict[str, str] | None) -> dict[str, str] | None:
        if headers is None:
            return None
        masked = dict(headers)
        authorization = masked.get("Authorization")
        if isinstance(authorization, str) and authorization.startswith("JWT "):
            masked["Authorization"] = "JWT ***"
        return masked

    @staticmethod
    def _mask_json_body(body: dict[str, Any] | None) -> dict[str, Any] | None:
        if body is None:
            return None
        masked = dict(body)
        if "password" in masked:
            masked["password"] = "***"
        return masked

    @staticmethod
    def _truncate_response_body(response: httpx.Response, limit: int = 4000) -> str:
        text = response.text
        if len(text) <= limit:
            return text
        return f"{text[:limit]}...<truncated>"
