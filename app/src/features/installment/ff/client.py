import socket
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx
from loguru import logger


class FFClientError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@contextmanager
def _resolve_host(hostname: str, ip: str) -> Iterator[None]:
    """curl --resolve hostname:443:ip — connect to internal IP, keep hostname for TLS/SNI."""
    original_getaddrinfo = socket.getaddrinfo

    def patched_getaddrinfo(
        host: str | bytes | None,
        port: str | int | None,
        family: int = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0,
    ):
        if host == hostname:
            host = ip
        return original_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = patched_getaddrinfo  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.getaddrinfo = original_getaddrinfo


class FFClient:
    _DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "SmartRemont-integrations-sr/1.0",
    }

    @classmethod
    def _build_headers(cls, headers: dict[str, str] | None) -> dict[str, str]:
        merged = dict(cls._DEFAULT_HEADERS)
        if headers:
            merged.update(headers)
        return merged

    @staticmethod
    def _auth_header(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    async def authenticate(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        resolve_ip: str | None = None,
    ) -> tuple[str, str | None]:
        payload = {
            "username": username,
            "password": password,
        }
        response = await self._request(
            method="POST",
            base_url=base_url,
            path="/ffc-api-auth/",
            json=payload,
            resolve_ip=resolve_ip,
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
        *,
        resolve_ip: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            base_url=base_url,
            path="/ffc-api-public/universal/additional/get-partner-info",
            params={"partner-id": partner_id},
            headers=self._auth_header(access_token),
            resolve_ip=resolve_ip,
        )

    async def apply_goods_loan_lead(
        self,
        base_url: str,
        access_token: str,
        payload: dict[str, Any],
        *,
        resolve_ip: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            base_url=base_url,
            path="/ffc-api-public/universal/apply/goods-loan-lead",
            json=payload,
            headers=self._auth_header(access_token),
            resolve_ip=resolve_ip,
        )

    async def get_goods_application_info(
        self,
        base_url: str,
        access_token: str,
        uuid: str,
        *,
        resolve_ip: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            base_url=base_url,
            path=f"/ffc-api-public/universal/additional/goods-application-info/{uuid}",
            headers=self._auth_header(access_token),
            resolve_ip=resolve_ip,
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
        resolve_ip: str | None = None,
    ) -> dict[str, Any]:
        request_url = f"{base_url.rstrip('/')}{path}"
        if params:
            request_url = f"{request_url}?{urlencode(params)}"

        outgoing_headers = self._build_headers(headers)
        hostname = urlparse(base_url.rstrip("/")).hostname

        logger.info(
            "FF HTTP request | method={method} url={url} resolve_ip={resolve_ip} headers={headers} body={body}",
            method=method,
            url=request_url,
            resolve_ip=resolve_ip,
            headers=self._mask_headers(outgoing_headers),
            body=self._mask_json_body(json),
        )

        timeout = httpx.Timeout(timeout=20.0, connect=10.0)
        resolve_ctx = (
            _resolve_host(hostname, resolve_ip)
            if resolve_ip and hostname
            else nullcontext()
        )
        try:
            with resolve_ctx:
                async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout) as client:
                    response = await client.request(
                        method=method,
                        url=path,
                        headers=outgoing_headers,
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
            raw_body = FFClient._truncate_response_body(response)
            if "cloudflare" in raw_body.lower() or "you have been blocked" in raw_body.lower():
                detail = (
                    f"Freedom Finance blocked the request (HTTP {response.status_code}, Cloudflare). "
                    "Set config.resolve_ip on provider FF (internal bank IP)."
                )

        logger.warning(
            "FF HTTP error | status={status} detail={detail} raw_body={body}",
            status=response.status_code,
            detail=detail,
            body=FFClient._truncate_response_body(response),
        )
        raise FFClientError(status_code=response.status_code, detail=detail)

    @staticmethod
    def _mask_headers(headers: dict[str, str] | None) -> dict[str, str] | None:
        if headers is None:
            return None
        masked = dict(headers)
        authorization = masked.get("Authorization")
        if isinstance(authorization, str) and (
            authorization.startswith("Bearer ") or authorization.startswith("JWT ")
        ):
            masked["Authorization"] = authorization.split(" ", 1)[0] + " ***"
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
