"""Write human-readable parity request/response logs (one file per test case)."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from httpx import Response

_REDACT_HEADERS = frozenset({"authorization"})


def parity_log_dir() -> Path | None:
    """Return log directory, or None if logging disabled."""
    if os.getenv("PARITY_LOG", "1").strip().lower() in {"0", "false", "no", "off"}:
        return None
    raw = os.getenv("PARITY_LOG_DIR", "app/tests/live/parity_logs").strip()
    path = Path(raw)
    if not path.is_absolute():
        # repo root = integrations-sr (parent of app/)
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / raw
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(case_id: str) -> str:
    return re.sub(r"[^\w.-]+", "_", case_id).strip("_") or "case"


def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _REDACT_HEADERS:
            out[key] = "***"
        else:
            out[key] = value
    return out


def _pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _format_headers(headers: dict[str, str]) -> str:
    if not headers:
        return "  (none)\n"
    lines = []
    for key, value in sorted(headers.items()):
        lines.append(f"  {key}: {value}")
    return "\n".join(lines) + "\n"


def _format_side_block(
    *,
    label: str,
    method: str,
    url: str,
    request_headers: dict[str, str],
    request_body: Any | None,
    query_params: dict[str, Any] | None,
    response: Response,
    parsed_body: Any,
) -> str:
    lines = [
        label,
        f"{method.upper()} {url}",
        "",
    ]
    if query_params:
        lines.extend(
            [
                "Query params:",
                _pretty_json(query_params),
                "",
            ]
        )
    if request_body is not None:
        lines.extend(
            [
                "Request body:",
                _pretty_json(request_body),
                "",
            ]
        )
    lines.extend(
        [
            "Request headers:",
            _format_headers(_redact_headers(request_headers)),
            f"Response status: {response.status_code}",
            f"Response size (bytes on wire): {len(response.content)}",
        ]
    )
    encoding = response.headers.get("content-encoding")
    if encoding:
        lines.append(f"Content-Encoding: {encoding}")
    lines.extend(
        [
            "",
            "Response headers:",
            _format_headers(dict(response.headers)),
            "Response JSON:",
            _pretty_json(parsed_body),
            "",
        ]
    )
    return "\n".join(lines)


def write_parity_log(
    *,
    case_id: str,
    method: str,
    office_url: str,
    office_params: dict[str, Any] | None,
    office_body: Any | None,
    office_headers: dict[str, str],
    office_response: Response,
    office_parsed: Any,
    fastapi_url: str,
    fastapi_params: dict[str, Any] | None,
    fastapi_body: Any | None,
    fastapi_headers: dict[str, str],
    fastapi_response: Response,
    fastapi_parsed: Any,
    passed: bool,
    error_message: str = "",
) -> Path | None:
    log_dir = parity_log_dir()
    if log_dir is None:
        return None

    if method.upper() == "GET" and office_params:
        office_full_url = f"{office_url}?{urlencode(office_params, doseq=True)}"
    else:
        office_full_url = office_url

    if method.upper() == "GET" and fastapi_params:
        fastapi_full_url = f"{fastapi_url}?{urlencode(fastapi_params, doseq=True)}"
    else:
        fastapi_full_url = fastapi_url

    status_match = office_response.status_code == fastapi_response.status_code
    json_match = office_parsed == fastapi_parsed

    parts = [
        f"Case: {case_id}",
        f"Timestamp (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"Result: {'PASS' if passed else 'FAIL'}",
        f"Status match: {'yes' if status_match else 'no'} "
        f"(OFFICE={office_response.status_code}, FASTAPI={fastapi_response.status_code})",
        f"JSON match: {'yes' if json_match else 'no'}",
        "",
    ]
    if error_message:
        parts.extend(["Error:", error_message, ""])

    parts.append(
        _format_side_block(
            label="OFFICE",
            method=method,
            url=office_full_url,
            request_headers=office_headers,
            request_body=office_body,
            query_params=office_params if method.upper() == "GET" else None,
            response=office_response,
            parsed_body=office_parsed,
        )
    )
    parts.append(
        _format_side_block(
            label="FASTAPI",
            method=method,
            url=fastapi_full_url,
            request_headers=fastapi_headers,
            request_body=fastapi_body,
            query_params=fastapi_params if method.upper() == "GET" else None,
            response=fastapi_response,
            parsed_body=fastapi_parsed,
        )
    )

    log_path = log_dir / f"{_safe_filename(case_id)}.log"
    log_path.write_text("\n".join(parts), encoding="utf-8")
    return log_path
