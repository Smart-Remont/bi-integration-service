import json
from typing import Any

import httpx
from src.config import kcell_config


class KcellClientError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class KcellClient:
    """HTTP client for Kcell Hermes SMS API (mirrors ``kcell_send_sms`` / ``kcell_check_batch_status``)."""

    async def send_batches(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        user = kcell_config.hermes_user
        password = kcell_config.hermes_password
        if not user or not password:
            raise KcellClientError("Kcell Hermes credentials are not configured (KCELL_HERMES_*)")

        url = f"{kcell_config.hermes_base_url.rstrip('/')}/batches"
        body = json.dumps(payload, ensure_ascii=False)
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    url,
                    content=body,
                    auth=(user, password),
                    headers={"Content-Type": "application/json"},
                )
            except httpx.RequestError as exc:
                raise KcellClientError(str(exc)) from exc

        raw_text = response.text
        if response.status_code >= 400:
            raise KcellClientError(f"Kcell Hermes HTTP {response.status_code}: {raw_text[:500]}")

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise KcellClientError(f"Invalid JSON from Kcell Hermes: {raw_text[:200]}") from exc

        if not isinstance(parsed, dict):
            raise KcellClientError("Unexpected Kcell Hermes response shape")

        return raw_text, parsed

    async def check_batch_status(self, batch_id: str) -> dict[str, Any]:
        user = kcell_config.batch_user
        password = kcell_config.batch_password
        if not user or not password:
            raise KcellClientError("Kcell batch credentials are not configured (KCELL_BATCH_*)")

        url = f"{kcell_config.batch_base_url.rstrip('/')}/{batch_id}"
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(url, auth=(user, password))
            except httpx.RequestError as exc:
                raise KcellClientError(str(exc)) from exc

        raw_text = response.text
        if response.status_code >= 400:
            raise KcellClientError(f"Kcell batch HTTP {response.status_code}: {raw_text[:500]}")

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise KcellClientError(f"Invalid JSON from Kcell batch API: {raw_text[:200]}") from exc

        if not isinstance(parsed, dict):
            raise KcellClientError("Unexpected Kcell batch response shape")

        return parsed
