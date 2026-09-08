"""PHP (devprod office) vs integrations-sr response parity helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx
import pytest

from .parity_reporter import write_parity_log

AuthKind = Literal["hs_bi", "ddu_export"]
PostBody = dict[str, Any] | list[Any]


@dataclass(frozen=True)
class ParityHttpExchange:
    status: int
    parsed: Any
    raw_text: str
    response: httpx.Response


@dataclass(frozen=True)
class GetParityCase:
    """One GET endpoint that must return identical JSON on PHP and Python."""

    id: str
    php_action: str
    py_path: str
    params: dict[str, Any]
    auth: AuthKind
    # all env vars must be set
    required_env: tuple[tuple[str, str], ...] = ()
    # at least one env var must be set (fills matching param)
    any_required_env: tuple[tuple[str, str], ...] = ()
    require_non_empty: tuple[str, ...] = ()


@dataclass(frozen=True)
class PostParityCase:
    """One POST endpoint that must return identical JSON on PHP and Python."""

    id: str
    php_action: str
    py_path: str
    body: PostBody
    auth: AuthKind = "hs_bi"
    required_env: tuple[tuple[str, str], ...] = ()
    # fill body[field] = [env_value] for array params (flat_guid, realEstateUUIDs, …)
    list_env: tuple[tuple[str, str], ...] = ()
    py_extra_headers: dict[str, str] = field(default_factory=dict)
    # JSON path that must be a non-empty list, e.g. ("data", "preset_list")
    require_non_empty: tuple[str, ...] = ()


def resolve_body(
    case: PostParityCase,
    *,
    env: dict[str, str | None],
) -> PostBody | None:
    """Fill JSON body fields from env; return None if required env is missing."""
    if isinstance(case.body, list):
        if not case.body:
            return []
        template = case.body[0]
        if not isinstance(template, dict):
            return list(case.body)
        row: dict[str, Any] = dict(template)
        for field_name, env_name in case.required_env:
            raw = (env.get(env_name) or "").strip()
            if not raw:
                return None
            row[field_name] = raw
        return [row]

    out = dict(case.body)
    for field_name, env_name in case.required_env:
        raw = (env.get(env_name) or "").strip()
        if not raw:
            return None
        if field_name in out and isinstance(out[field_name], list) and field_name.endswith("_guids") is False:
            # e.g. flat_guid: [""] -> [value]
            if len(out[field_name]) == 1 and out[field_name][0] == "":
                out[field_name] = [raw]
                continue
        if isinstance(out.get(field_name), int) and raw.isdigit():
            out[field_name] = int(raw)
        else:
            out[field_name] = raw
    for field_name, env_name in case.list_env:
        raw = (env.get(env_name) or "").strip()
        if not raw:
            return None
        out[field_name] = [raw]
    return out


def resolve_params(
    case: GetParityCase,
    *,
    env: dict[str, str | None],
) -> dict[str, Any] | None:
    """Fill params from env; return None if required env is missing."""
    out = dict(case.params)

    for param_name, env_name in case.required_env:
        raw = (env.get(env_name) or "").strip()
        if not raw:
            return None
        out[param_name] = int(raw) if param_name == "client_request_id" else raw

    if case.any_required_env:
        filled = False
        for param_name, env_name in case.any_required_env:
            raw = (env.get(env_name) or "").strip()
            if raw:
                out[param_name] = raw
                filled = True
        if not filled:
            return None

    return out


def assert_status_parity(php_status: int, py_status: int, *, case_id: str) -> None:
    if php_status != py_status:
        pytest.fail(
            f"[{case_id}] HTTP status mismatch: PHP={php_status}, integrations-sr={py_status}"
        )


def assert_json_parity(
    php_body: Any,
    py_body: Any,
    *,
    case_id: str,
    php_raw: str = "",
    py_raw: str = "",
) -> None:
    """Strict deep equality — contract must match 100%."""
    if php_body == py_body:
        return

    php_pretty = json.dumps(php_body, ensure_ascii=False, indent=2, sort_keys=True)
    py_pretty = json.dumps(py_body, ensure_ascii=False, indent=2, sort_keys=True)
    msg = (
        f"[{case_id}] JSON body mismatch (100% parity required)\n"
        f"--- PHP (devprod) ---\n{php_pretty}\n"
        f"--- integrations-sr ---\n{py_pretty}\n"
    )
    if php_raw and py_raw and php_raw != py_raw:
        msg += (
            f"--- raw PHP ---\n{php_raw[:2000]}\n"
            f"--- raw PY ---\n{py_raw[:2000]}\n"
        )
    pytest.fail(msg)


def _value_at_path(data: Any, path: tuple[str, ...]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def assert_non_empty(
    body: Any,
    *,
    case_id: str,
    path: tuple[str, ...],
    side: str,
) -> None:
    value = _value_at_path(body, path)
    if isinstance(value, list) and len(value) > 0:
        return
    pytest.fail(
        f"[{case_id}] Expected non-empty list at {'.'.join(path)} in {side} response, got {value!r}"
    )


def _headers_for_log(auth: dict[str, str], extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json", **auth}
    if extra:
        headers.update(extra)
    return headers


def parse_legacy_php_json(text: str) -> Any:
    """Parse JSON from PHP body that may include HTML warnings before the payload."""
    stripped = text.strip()
    if not stripped:
        raise json.JSONDecodeError("Empty response", stripped, 0)
    start_obj = stripped.find("{")
    start_arr = stripped.find("[")
    if start_obj < 0 and start_arr < 0:
        raise json.JSONDecodeError("No JSON in response", stripped, 0)
    if start_arr >= 0 and (start_obj < 0 or start_arr < start_obj):
        start = start_arr
    else:
        start = start_obj
    decoder = json.JSONDecoder()
    obj, _end = decoder.raw_decode(stripped[start:])
    return obj


def load_response_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError:
        return parse_legacy_php_json(response.text)


async def fetch_get(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any],
    headers: dict[str, str],
) -> ParityHttpExchange:
    response = await client.get(url, params=params, headers=headers)
    try:
        body = load_response_json(response)
    except json.JSONDecodeError:
        pytest.fail(f"Non-JSON from {url}: {response.status_code} {response.text[:500]}")
    return ParityHttpExchange(
        status=response.status_code,
        parsed=body,
        raw_text=response.text,
        response=response,
    )


async def fetch_post(
    client: httpx.AsyncClient,
    url: str,
    *,
    body: PostBody,
    headers: dict[str, str],
) -> ParityHttpExchange:
    response = await client.post(url, json=body, headers=headers)
    try:
        parsed = load_response_json(response)
    except json.JSONDecodeError:
        pytest.fail(f"Non-JSON from {url}: {response.status_code} {response.text[:500]}")
    return ParityHttpExchange(
        status=response.status_code,
        parsed=parsed,
        raw_text=response.text,
        response=response,
    )


def _finalize_parity(
    *,
    case_id: str,
    method: str,
    office_url: str,
    office_params: dict[str, Any] | None,
    office_body: Any | None,
    office_headers: dict[str, str],
    php: ParityHttpExchange,
    fastapi_url: str,
    fastapi_params: dict[str, Any] | None,
    fastapi_body: Any | None,
    fastapi_headers: dict[str, str],
    py: ParityHttpExchange,
    require_non_empty: tuple[str, ...] = (),
) -> None:
    error: str | None = None
    try:
        assert_status_parity(php.status, py.status, case_id=case_id)
        if require_non_empty:
            assert_non_empty(php.parsed, case_id=case_id, path=require_non_empty, side="OFFICE")
            assert_non_empty(py.parsed, case_id=case_id, path=require_non_empty, side="FASTAPI")
        assert_json_parity(
            php.parsed,
            py.parsed,
            case_id=case_id,
            php_raw=php.raw_text,
            py_raw=py.raw_text,
        )
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        write_parity_log(
            case_id=case_id,
            method=method,
            office_url=office_url,
            office_params=office_params,
            office_body=office_body,
            office_headers=office_headers,
            office_response=php.response,
            office_parsed=php.parsed,
            fastapi_url=fastapi_url,
            fastapi_params=fastapi_params,
            fastapi_body=fastapi_body,
            fastapi_headers=fastapi_headers,
            fastapi_response=py.response,
            fastapi_parsed=py.parsed,
            passed=error is None,
            error_message=error or "",
        )


async def assert_post_parity(
    *,
    case: PostParityCase,
    body: PostBody,
    office_base_url: str,
    integrations_base_url: str,
    hs_bi_auth: dict[str, str],
    ddu_export_auth: dict[str, str],
    client: httpx.AsyncClient,
) -> None:
    auth = hs_bi_auth if case.auth == "hs_bi" else ddu_export_auth
    php_url = f"{office_base_url}/integration/{case.php_action}"
    py_url = f"{integrations_base_url}{case.py_path}"
    py_extra = case.py_extra_headers
    office_headers = _headers_for_log(auth)
    fastapi_headers = _headers_for_log(auth, py_extra)

    php = await fetch_post(client, php_url, body=body, headers=auth)
    py_headers = {**auth, **py_extra}
    py = await fetch_post(client, py_url, body=body, headers=py_headers)

    _finalize_parity(
        case_id=case.id,
        method="POST",
        office_url=php_url,
        office_params=None,
        office_body=body,
        office_headers=office_headers,
        php=php,
        fastapi_url=py_url,
        fastapi_params=None,
        fastapi_body=body,
        fastapi_headers=fastapi_headers,
        py=py,
        require_non_empty=case.require_non_empty,
    )


async def assert_get_parity(
    *,
    case: GetParityCase,
    params: dict[str, Any],
    office_base_url: str,
    integrations_base_url: str,
    hs_bi_auth: dict[str, str],
    ddu_export_auth: dict[str, str],
    client: httpx.AsyncClient,
) -> None:
    auth = hs_bi_auth if case.auth == "hs_bi" else ddu_export_auth
    php_url = f"{office_base_url}/integration/{case.php_action}"
    py_url = f"{integrations_base_url}{case.py_path}"
    office_headers = _headers_for_log(auth)
    # GET has no JSON body; avoid Content-Type in log unless sent
    office_headers = {k: v for k, v in auth.items()}
    fastapi_headers = dict(office_headers)

    php = await fetch_get(client, php_url, params=params, headers=auth)
    py = await fetch_get(client, py_url, params=params, headers=auth)

    _finalize_parity(
        case_id=case.id,
        method="GET",
        office_url=php_url,
        office_params=params,
        office_body=None,
        office_headers=office_headers,
        php=php,
        fastapi_url=py_url,
        fastapi_params=params,
        fastapi_body=None,
        fastapi_headers=fastapi_headers,
        py=py,
        require_non_empty=case.require_non_empty,
    )
