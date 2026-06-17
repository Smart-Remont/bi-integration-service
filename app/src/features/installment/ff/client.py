from typing import Any

import httpx


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
        timeout = httpx.Timeout(timeout=20.0, connect=10.0)
        async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=path,
                headers=headers,
                params=params,
                json=json,
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

        raise FFClientError(status_code=response.status_code, detail=detail)
