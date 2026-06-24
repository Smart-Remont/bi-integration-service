from typing import Any
from urllib.parse import urlencode, urlparse

import httpx
from loguru import logger


class FFClientError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


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

    @staticmethod
    def _transport_target(
        base_url: str,
        resolve_ip: str | None,
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """curl --resolve host:443:ip — TCP to internal IP, TLS SNI + Host = public hostname."""
        parsed = urlparse(base_url.rstrip("/"))
        hostname = parsed.hostname
        if not resolve_ip or not hostname:
            return base_url.rstrip("/"), {}, {}

        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        connect_base = f"{parsed.scheme}://{resolve_ip}:{port}"
        return connect_base, {"Host": hostname}, {"sni_hostname": hostname}

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
        logical_url = f"{base_url.rstrip('/')}{path}"
        if params:
            logical_url = f"{logical_url}?{urlencode(params)}"

        connect_base, resolve_headers, extensions = self._transport_target(base_url, resolve_ip)
        outgoing_headers = self._build_headers(headers)
        outgoing_headers.update(resolve_headers)
        connect_url = f"{connect_base}{path}"
        if params:
            connect_url = f"{connect_url}?{urlencode(params)}"

        logger.info(
            "FF HTTP request | method={method} url={url} connect_url={connect_url} resolve_ip={resolve_ip} "
            "headers={headers} body={body}",
            method=method,
            url=logical_url,
            connect_url=connect_url,
            resolve_ip=resolve_ip,
            headers=self._mask_headers(outgoing_headers),
            body=self._mask_json_body(json),
        )

        timeout = httpx.Timeout(timeout=20.0, connect=10.0)
        try:
            async with httpx.AsyncClient(
                base_url=connect_base, timeout=timeout, follow_redirects=True
            ) as client:
                response = await client.request(
                    method=method,
                    url=path,
                    headers=outgoing_headers,
                    params=params,
                    json=json,
                    extensions=extensions,
                )
        except httpx.RequestError as exc:
            logger.error(
                "FF HTTP transport error | connect_url={url} error={error}",
                url=connect_url,
                error=exc,
            )
            raise FFClientError(
                status_code=502,
                detail=f"Freedom Finance request failed: {exc}",
            ) from exc

        logger.info(
            "FF HTTP response | connect_url={url} status={status} body={body}",
            url=connect_url,
            status=response.status_code,
            body=self._truncate_response_body(response),
        )
        return self._parse_response(response, resolve_ip=resolve_ip)

    @staticmethod
    def _parse_response(response: httpx.Response, *, resolve_ip: str | None = None) -> dict[str, Any]:
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
                if resolve_ip:
                    detail = (
                        f"Freedom Finance blocked the request (HTTP {response.status_code}, Cloudflare) "
                        f"despite resolve_ip={resolve_ip}. "
                        "Ensure the container can reach the internal bank IP (host network or extra_hosts)."
                    )
                else:
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
