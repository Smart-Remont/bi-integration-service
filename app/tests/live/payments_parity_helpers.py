"""PHP (devprod) vs integrations-sr parity helpers for Payments (XML / plain)."""

from __future__ import annotations

import json
import os
import re
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
import pytest

from .parity_reporter import parity_log_dir


@dataclass(frozen=True)
class KaspiParityCase:
    id: str
    php_action: str
    py_path: str
    params: dict[str, Any]
    required_env: tuple[tuple[str, str], ...] = ()
    generate_txn_id: bool = False


@dataclass(frozen=True)
class KaspiParityExchange:
    status: int
    parsed: dict[str, Any]
    raw_text: str
    response: httpx.Response


def _payments_log_dir() -> Path | None:
    base = parity_log_dir()
    if base is None:
        return None
    sub = base / "payments"
    sub.mkdir(parents=True, exist_ok=True)
    return sub


def _safe_filename(case_id: str) -> str:
    return re.sub(r"[^\w.-]+", "_", case_id).strip("_") or "case"


def extract_kaspi_xml(text: str) -> str:
    """Strip PHP warnings/notices that may prefix or suffix Kaspi XML."""
    stripped = text.strip()
    if not stripped:
        return stripped
    start = stripped.find("<?xml")
    if start < 0:
        start = stripped.find("<response")
    if start < 0:
        return stripped
    end = stripped.rfind("</response>")
    if end >= 0:
        return stripped[start : end + len("</response>")]
    return stripped[start:]


def kaspi_xml_to_dict(text: str) -> dict[str, Any]:
    """Parse Kaspi XML into a canonical dict for deep comparison."""
    xml_text = extract_kaspi_xml(text)
    if not xml_text:
        return {}
    root = ET.fromstring(xml_text)
    out: dict[str, Any] = {}
    for child in root:
        if child.tag == "fields":
            fields: list[dict[str, str]] = []
            for field_el in child:
                fields.append(
                    {
                        "tag": field_el.tag,
                        "name": field_el.get("name") or "",
                        "text": (field_el.text or "").strip(),
                    }
                )
            out["fields"] = sorted(fields, key=lambda item: item["tag"])
        else:
            out[child.tag] = (child.text or "").strip()
    return out


def assert_kaspi_xml_parity(
    php_body: dict[str, Any],
    py_body: dict[str, Any],
    *,
    case_id: str,
    php_raw: str = "",
    py_raw: str = "",
) -> None:
    if php_body == py_body:
        return
    php_pretty = json.dumps(php_body, ensure_ascii=False, indent=2, sort_keys=True)
    py_pretty = json.dumps(py_body, ensure_ascii=False, indent=2, sort_keys=True)
    msg = (
        f"[{case_id}] Kaspi XML mismatch (canonical compare)\n"
        f"--- PHP (devprod) ---\n{php_pretty}\n"
        f"--- integrations-sr ---\n{py_pretty}\n"
    )
    if php_raw and py_raw:
        msg += f"--- raw PHP ---\n{php_raw[:2000]}\n--- raw PY ---\n{py_raw[:2000]}\n"
    pytest.fail(msg)


def resolve_kaspi_params(
    case: KaspiParityCase,
    *,
    env: dict[str, str | None],
) -> dict[str, Any] | None:
    out = dict(case.params)
    for param_name, env_name in case.required_env:
        raw = (env.get(env_name) or "").strip()
        if not raw:
            return None
        if param_name == "account" and raw.isdigit():
            out[param_name] = int(raw)
        elif param_name == "sum" and raw.isdigit():
            out[param_name] = int(raw)
        else:
            out[param_name] = raw
    if case.generate_txn_id:
        out["txn_id"] = f"PARITY-KASPI-{case.id}-{uuid.uuid4().hex[:8]}"
    return out


def _parse_kaspi_response(url: str, response: httpx.Response) -> KaspiParityExchange:
    raw = response.text
    xml_text = extract_kaspi_xml(raw)
    if not xml_text or "<response" not in xml_text:
        return KaspiParityExchange(
            status=response.status_code,
            parsed={},
            raw_text=raw,
            response=response,
        )
    try:
        parsed = kaspi_xml_to_dict(xml_text)
    except ET.ParseError as exc:
        pytest.fail(
            f"Invalid XML from {url}: {response.status_code} {raw[:500]} "
            f"(extracted: {xml_text[:300]!r}, {exc})"
        )
    return KaspiParityExchange(
        status=response.status_code,
        parsed=parsed,
        raw_text=raw,
        response=response,
    )


async def fetch_kaspi_get(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any],
) -> KaspiParityExchange:
    response = await client.get(url, params=params)
    return _parse_kaspi_response(url, response)


def _write_payments_parity_log(
    *,
    case_id: str,
    office_url: str,
    office_params: dict[str, Any],
    office: KaspiParityExchange,
    fastapi_url: str,
    fastapi: KaspiParityExchange,
    passed: bool,
    error_message: str = "",
    fastapi_params: dict[str, Any] | None = None,
) -> Path | None:
    log_dir = _payments_log_dir()
    if log_dir is None:
        return None

    py_params = office_params if fastapi_params is None else fastapi_params
    office_full = f"{office_url}?{urlencode(office_params, doseq=True)}"
    fastapi_full = f"{fastapi_url}?{urlencode(py_params, doseq=True)}"
    status_match = office.status == fastapi.status
    xml_match = office.parsed == fastapi.parsed

    parts = [
        f"Case: {case_id}",
        f"Timestamp (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"Result: {'PASS' if passed else 'FAIL'}",
        f"Status match: {'yes' if status_match else 'no'} "
        f"(OFFICE={office.status}, FASTAPI={fastapi.status})",
        f"XML match: {'yes' if xml_match else 'no'}",
        "",
    ]
    if error_message:
        parts.extend(["Error:", error_message, ""])

    for label, url, exchange in (
        ("OFFICE", office_full, office),
        ("FASTAPI", fastapi_full, fastapi),
    ):
        parts.extend(
            [
                label,
                f"GET {url}",
                "",
                f"Response status: {exchange.status}",
                "Response XML (canonical):",
                json.dumps(exchange.parsed, ensure_ascii=False, indent=2, sort_keys=True),
                "",
                "Response raw:",
                exchange.raw_text[:4000],
                "",
            ]
        )

    log_path = log_dir / f"{_safe_filename(case_id)}.log"
    log_path.write_text("\n".join(parts), encoding="utf-8")
    return log_path


async def assert_kaspi_get_parity(
    *,
    case: KaspiParityCase,
    params: dict[str, Any],
    office_base_url: str,
    integrations_base_url: str,
    client: httpx.AsyncClient,
) -> None:
    php_url = f"{office_base_url}/client/{case.php_action}"
    py_url = f"{integrations_base_url}{case.py_path}"

    php = await fetch_kaspi_get(client, php_url, params=params)
    py = await fetch_kaspi_get(client, py_url, params=params)

    if not php.parsed:
        pytest.skip(
            f"[{case.id}] PHP returned no Kaspi XML from {php_url} "
            "(devprod log_kaspi dir missing or wrong legacy URL?)"
        )
    if py.status == 403 or py.parsed.get("result") == "403":
        pytest.skip(
            f"[{case.id}] FastAPI IP blocked — set KASPI_ALLOWED_IPS= (empty) "
            "in app/.env and restart uvicorn"
        )
    if not py.parsed:
        pytest.fail(f"[{case.id}] FastAPI returned no Kaspi XML from {py_url}")

    error: str | None = None
    try:
        if php.status != py.status:
            pytest.fail(
                f"[{case.id}] HTTP status mismatch: PHP={php.status}, integrations-sr={py.status}"
            )
        assert_kaspi_xml_parity(
            php.parsed,
            py.parsed,
            case_id=case.id,
            php_raw=php.raw_text,
            py_raw=py.raw_text,
        )
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        _write_payments_parity_log(
            case_id=case.id,
            office_url=php_url,
            office_params=params,
            office=php,
            fastapi_url=py_url,
            fastapi=py,
            passed=error is None,
            error_message=error or "",
        )


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse JSON object from body that may include PHP warnings."""
    stripped = text.strip()
    start = stripped.find("{")
    if start < 0:
        return {}
    decoder = json.JSONDecoder()
    obj, _end = decoder.raw_decode(stripped[start:])
    if isinstance(obj, dict):
        return obj
    return {}


@dataclass(frozen=True)
class CloudPaymentsParityCase:
    id: str
    mode: str
    body: str
    required_env: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class CloudPaymentsParityExchange:
    status: int
    parsed: dict[str, Any]
    raw_text: str
    response: httpx.Response


def resolve_cp_body(case: CloudPaymentsParityCase, *, env: dict[str, str | None]) -> str | None:
    body = case.body
    for placeholder, env_name in case.required_env:
        raw = (env.get(env_name) or "").strip()
        if not raw:
            return None
        body = body.replace(placeholder, raw)
    return body


def assert_cp_json_parity(
    php_body: dict[str, Any],
    py_body: dict[str, Any],
    *,
    case_id: str,
    php_raw: str = "",
    py_raw: str = "",
) -> None:
    if php_body == py_body:
        return
    php_pretty = json.dumps(php_body, ensure_ascii=False, indent=2, sort_keys=True)
    py_pretty = json.dumps(py_body, ensure_ascii=False, indent=2, sort_keys=True)
    msg = (
        f"[{case_id}] CloudPayments JSON mismatch\n"
        f"--- PHP (devprod) ---\n{php_pretty}\n"
        f"--- integrations-sr ---\n{py_pretty}\n"
    )
    if php_raw and py_raw:
        msg += f"--- raw PHP ---\n{php_raw[:2000]}\n--- raw PY ---\n{py_raw[:2000]}\n"
    pytest.fail(msg)


async def fetch_cp_post(
    client: httpx.AsyncClient,
    url: str,
    *,
    body: str,
) -> CloudPaymentsParityExchange:
    response = await client.post(
        url,
        content=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    parsed = extract_json_object(response.text)
    return CloudPaymentsParityExchange(
        status=response.status_code,
        parsed=parsed,
        raw_text=response.text,
        response=response,
    )


def _write_cp_parity_log(
    *,
    case_id: str,
    office_url: str,
    body: str,
    office: CloudPaymentsParityExchange,
    fastapi_url: str,
    fastapi: CloudPaymentsParityExchange,
    passed: bool,
    error_message: str = "",
) -> Path | None:
    log_dir = _payments_log_dir()
    if log_dir is None:
        return None

    status_match = office.status == fastapi.status
    json_match = office.parsed == fastapi.parsed
    parts = [
        f"Case: {case_id}",
        f"Timestamp (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"Result: {'PASS' if passed else 'FAIL'}",
        f"Status match: {'yes' if status_match else 'no'} "
        f"(OFFICE={office.status}, FASTAPI={fastapi.status})",
        f"JSON match: {'yes' if json_match else 'no'}",
        "",
        "Request body:",
        body,
        "",
    ]
    if error_message:
        parts.extend(["Error:", error_message, ""])

    for label, url, exchange in (
        ("OFFICE", office_url, office),
        ("FASTAPI", fastapi_url, fastapi),
    ):
        parts.extend(
            [
                label,
                f"POST {url}",
                "",
                f"Response status: {exchange.status}",
                "Response JSON:",
                json.dumps(exchange.parsed, ensure_ascii=False, indent=2, sort_keys=True),
                "",
                "Response raw:",
                exchange.raw_text[:4000],
                "",
            ]
        )

    log_path = log_dir / f"{_safe_filename(case_id)}.log"
    log_path.write_text("\n".join(parts), encoding="utf-8")
    return log_path


async def assert_cloudpayments_post_parity(
    *,
    case: CloudPaymentsParityCase,
    body: str,
    office_base_url: str,
    integrations_base_url: str,
    client: httpx.AsyncClient,
) -> None:
    php_url = f"{office_base_url}/client/cp-response/mode/{case.mode}"
    py_url = f"{integrations_base_url}/api/payments/cloudpayments/mode/{case.mode}"

    php = await fetch_cp_post(client, php_url, body=body)
    py = await fetch_cp_post(client, py_url, body=body)

    if not php.parsed:
        pytest.skip(
            f"[{case.id}] PHP returned no JSON from {php_url} "
            "(check legacy cp-response route on devprod)"
        )
    if not py.parsed:
        pytest.fail(f"[{case.id}] FastAPI returned no JSON from {py_url}")

    error: str | None = None
    try:
        if php.status != py.status:
            pytest.fail(
                f"[{case.id}] HTTP status mismatch: PHP={php.status}, integrations-sr={py.status}"
            )
        assert_cp_json_parity(
            php.parsed,
            py.parsed,
            case_id=case.id,
            php_raw=php.raw_text,
            py_raw=py.raw_text,
        )
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        _write_cp_parity_log(
            case_id=case.id,
            office_url=php_url,
            body=body,
            office=php,
            fastapi_url=py_url,
            fastapi=py,
            passed=error is None,
            error_message=error or "",
        )


def cp_env_snapshot() -> dict[str, str | None]:
    return {
        "TEST_CP_REQUEST_HASH": os.getenv("TEST_CP_REQUEST_HASH"),
        "TEST_CP_INVOICE_HASH": os.getenv("TEST_CP_INVOICE_HASH"),
        "TEST_CP_AMOUNT": os.getenv("TEST_CP_AMOUNT"),
    }


def extract_plain_body(text: str) -> str:
    """Plain-text payment responses; strip PHP warnings (last non-HTML line)."""
    stripped = text.strip()
    if not stripped:
        return stripped
    if "<" not in stripped:
        return stripped
    for line in reversed(stripped.splitlines()):
        candidate = line.strip()
        if candidate and "<" not in candidate:
            return candidate
    return stripped


@dataclass(frozen=True)
class SberParityCase:
    id: str
    php_action: str
    py_path: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SberParityExchange:
    status: int
    body: str
    raw_text: str
    response: httpx.Response


def assert_plain_parity(php_body: str, py_body: str, *, case_id: str) -> None:
    if php_body == py_body:
        return
    pytest.fail(
        f"[{case_id}] Plain body mismatch: PHP={php_body!r}, integrations-sr={py_body!r}"
    )


async def fetch_sber_get(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any],
) -> SberParityExchange:
    response = await client.get(url, params=params)
    body = extract_plain_body(response.text)
    return SberParityExchange(
        status=response.status_code,
        body=body,
        raw_text=response.text,
        response=response,
    )


def _write_sber_parity_log(
    *,
    case_id: str,
    office_url: str,
    params: dict[str, Any],
    office: SberParityExchange,
    fastapi_url: str,
    fastapi: SberParityExchange,
    passed: bool,
    error_message: str = "",
) -> Path | None:
    log_dir = _payments_log_dir()
    if log_dir is None:
        return None

    office_full = f"{office_url}?{urlencode(params, doseq=True)}" if params else office_url
    fastapi_full = f"{fastapi_url}?{urlencode(params, doseq=True)}" if params else fastapi_url
    parts = [
        f"Case: {case_id}",
        f"Timestamp (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"Result: {'PASS' if passed else 'FAIL'}",
        f"Status match: {'yes' if office.status == fastapi.status else 'no'} "
        f"(OFFICE={office.status}, FASTAPI={fastapi.status})",
        f"Body match: {'yes' if office.body == fastapi.body else 'no'}",
        "",
    ]
    if error_message:
        parts.extend(["Error:", error_message, ""])

    for label, url, exchange in (
        ("OFFICE", office_full, office),
        ("FASTAPI", fastapi_full, fastapi),
    ):
        parts.extend(
            [
                label,
                f"GET {url}",
                "",
                f"Response status: {exchange.status}",
                f"Response body: {exchange.body!r}",
                "",
                "Response raw:",
                exchange.raw_text[:4000],
                "",
            ]
        )

    log_path = log_dir / f"{_safe_filename(case_id)}.log"
    log_path.write_text("\n".join(parts), encoding="utf-8")
    return log_path


def assert_kaspi_pay_success(parsed: dict[str, Any], *, side: str, case_id: str) -> None:
    if parsed.get("result") != "0":
        pytest.fail(f"[{case_id}] Expected Kaspi pay success from {side}, got {parsed!r}")
    if "prv_txn" not in parsed:
        pytest.fail(f"[{case_id}] Expected prv_txn from {side}, got {parsed!r}")


def assert_kaspi_pay_shape_parity(
    php_body: dict[str, Any],
    py_body: dict[str, Any],
    *,
    case_id: str,
) -> None:
    """Both sides paid successfully; dynamic ids (prv_txn, bin) may differ."""
    expected_keys = {"txn_id", "prv_txn", "sum", "result", "bin", "comment"}
    php_keys = set(php_body.keys())
    py_keys = set(py_body.keys())
    if php_keys != py_keys:
        pytest.fail(
            f"[{case_id}] Kaspi pay XML keys mismatch: PHP={sorted(php_keys)}, "
            f"PY={sorted(py_keys)} (expected {sorted(expected_keys)})"
        )
    if php_keys != expected_keys:
        pytest.fail(f"[{case_id}] Unexpected Kaspi pay keys: {sorted(php_keys)}")
    if php_body.get("comment") != "OK" or py_body.get("comment") != "OK":
        pytest.fail(f"[{case_id}] Expected comment=OK on both sides")
    if php_body.get("result") != "0" or py_body.get("result") != "0":
        pytest.fail(f"[{case_id}] Expected result=0 on both sides")


async def assert_kaspi_pay_mutating_parity(
    *,
    case_id: str,
    php_action: str,
    py_path: str,
    php_params: dict[str, Any],
    py_params: dict[str, Any],
    office_base_url: str,
    integrations_base_url: str,
    client: httpx.AsyncClient,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Each side pays its own fixture (same txn_id cannot be consumed twice)."""
    php_url = f"{office_base_url}/client/{php_action}"
    py_url = f"{integrations_base_url}{py_path}"

    php = await fetch_kaspi_get(client, php_url, params=php_params)
    py = await fetch_kaspi_get(client, py_url, params=py_params)

    if not php.parsed:
        pytest.skip(f"[{case_id}] PHP returned no Kaspi XML from {php_url}")
    if py.status == 403 or py.parsed.get("result") == "403":
        pytest.skip(f"[{case_id}] FastAPI IP blocked — set KASPI_ALLOWED_IPS= in app/.env")
    if not py.parsed:
        pytest.fail(f"[{case_id}] FastAPI returned no Kaspi XML from {py_url}")

    error: str | None = None
    try:
        if php.status != py.status:
            pytest.fail(
                f"[{case_id}] HTTP status mismatch: PHP={php.status}, integrations-sr={py.status}"
            )
        assert_kaspi_pay_success(php.parsed, side="OFFICE", case_id=case_id)
        assert_kaspi_pay_success(py.parsed, side="FASTAPI", case_id=case_id)
        assert_kaspi_pay_shape_parity(php.parsed, py.parsed, case_id=case_id)
        if str(php.parsed.get("sum")) != str(php_params.get("sum")):
            pytest.fail(f"[{case_id}] PHP sum mismatch")
        if str(py.parsed.get("sum")) != str(py_params.get("sum")):
            pytest.fail(f"[{case_id}] FastAPI sum mismatch")
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        _write_payments_parity_log(
            case_id=case_id,
            office_url=php_url,
            office_params=php_params,
            office=php,
            fastapi_url=py_url,
            fastapi=py,
            passed=error is None,
            error_message=error or "",
            fastapi_params=py_params,
        )
    return php.parsed, py.parsed


async def assert_cp_mutating_post_parity(
    *,
    case_id: str,
    mode: str,
    body: str,
    office_base_url: str,
    integrations_base_url: str,
    client: httpx.AsyncClient,
    expect_code: int | None = 0,
) -> None:
    php_url = f"{office_base_url}/client/cp-response/mode/{mode}"
    py_url = f"{integrations_base_url}/api/payments/cloudpayments/mode/{mode}"

    php = await fetch_cp_post(client, php_url, body=body)
    py = await fetch_cp_post(client, py_url, body=body)

    if not php.parsed:
        pytest.skip(f"[{case_id}] PHP returned no JSON from {php_url}")
    if not py.parsed:
        pytest.fail(f"[{case_id}] FastAPI returned no JSON from {py_url}")

    error: str | None = None
    try:
        if php.status != py.status:
            pytest.fail(
                f"[{case_id}] HTTP status mismatch: PHP={php.status}, integrations-sr={py.status}"
            )
        assert_cp_json_parity(
            php.parsed,
            py.parsed,
            case_id=case_id,
            php_raw=php.raw_text,
            py_raw=py.raw_text,
        )
        if expect_code is not None and php.parsed.get("code") != expect_code:
            pytest.fail(
                f"[{case_id}] Expected code {expect_code} from PHP, got {php.parsed.get('code')!r}"
            )
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        _write_cp_parity_log(
            case_id=case_id,
            office_url=php_url,
            body=body,
            office=php,
            fastapi_url=py_url,
            fastapi=py,
            passed=error is None,
            error_message=error or "",
        )


def kaspi_mutating_env_snapshot() -> dict[str, str | None]:
    return {
        "TEST_KASPI_MUTATING_PHP_CLIENT_REQUEST_ID": os.getenv(
            "TEST_KASPI_MUTATING_PHP_CLIENT_REQUEST_ID"
        ),
        "TEST_KASPI_MUTATING_PHP_IIN": os.getenv("TEST_KASPI_MUTATING_PHP_IIN"),
        "TEST_KASPI_MUTATING_PHP_SUM": os.getenv("TEST_KASPI_MUTATING_PHP_SUM"),
        "TEST_KASPI_MUTATING_PY_CLIENT_REQUEST_ID": os.getenv(
            "TEST_KASPI_MUTATING_PY_CLIENT_REQUEST_ID"
        ),
        "TEST_KASPI_MUTATING_PY_IIN": os.getenv("TEST_KASPI_MUTATING_PY_IIN"),
        "TEST_KASPI_MUTATING_PY_SUM": os.getenv("TEST_KASPI_MUTATING_PY_SUM"),
        "TEST_KASPI_MUTATING_PHP_PAYMENT_ID": os.getenv("TEST_KASPI_MUTATING_PHP_PAYMENT_ID"),
        "TEST_KASPI_MUTATING_PHP_PAYMENT_IIN": os.getenv("TEST_KASPI_MUTATING_PHP_PAYMENT_IIN"),
        "TEST_KASPI_MUTATING_PHP_PAYMENT_SUM": os.getenv("TEST_KASPI_MUTATING_PHP_PAYMENT_SUM"),
        "TEST_KASPI_MUTATING_PY_PAYMENT_ID": os.getenv("TEST_KASPI_MUTATING_PY_PAYMENT_ID"),
        "TEST_KASPI_MUTATING_PY_PAYMENT_IIN": os.getenv("TEST_KASPI_MUTATING_PY_PAYMENT_IIN"),
        "TEST_KASPI_MUTATING_PY_PAYMENT_SUM": os.getenv("TEST_KASPI_MUTATING_PY_PAYMENT_SUM"),
        "TEST_CP_MUTATING_REQUEST_HASH": os.getenv("TEST_CP_MUTATING_REQUEST_HASH"),
        "TEST_CP_MUTATING_INVOICE_HASH": os.getenv("TEST_CP_MUTATING_INVOICE_HASH"),
        "TEST_CP_MUTATING_AMOUNT": os.getenv("TEST_CP_MUTATING_AMOUNT"),
        "TEST_CP_MUTATING_PAYMENT_REQUEST_HASH": os.getenv("TEST_CP_MUTATING_PAYMENT_REQUEST_HASH"),
        "TEST_CP_MUTATING_PAYMENT_INVOICE_HASH": os.getenv("TEST_CP_MUTATING_PAYMENT_INVOICE_HASH"),
        "TEST_CP_MUTATING_PAYMENT_AMOUNT": os.getenv("TEST_CP_MUTATING_PAYMENT_AMOUNT"),
        "TEST_SBER_MUTATING_ORDER_NUMBER": os.getenv("TEST_SBER_MUTATING_ORDER_NUMBER"),
    }


async def assert_sber_get_parity(
    *,
    case: SberParityCase,
    office_base_url: str,
    integrations_base_url: str,
    client: httpx.AsyncClient,
) -> None:
    php_url = f"{office_base_url}/integration/{case.php_action}"
    py_url = f"{integrations_base_url}{case.py_path}"

    php = await fetch_sber_get(client, php_url, params=case.params)
    py = await fetch_sber_get(client, py_url, params=case.params)

    if not php.body:
        pytest.skip(f"[{case.id}] PHP returned empty body from {php_url}")

    error: str | None = None
    try:
        if php.status != py.status:
            pytest.fail(
                f"[{case.id}] HTTP status mismatch: PHP={php.status}, integrations-sr={py.status}"
            )
        assert_plain_parity(php.body, py.body, case_id=case.id)
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        _write_sber_parity_log(
            case_id=case.id,
            office_url=php_url,
            params=case.params,
            office=php,
            fastapi_url=py_url,
            fastapi=py,
            passed=error is None,
            error_message=error or "",
        )


def kaspi_env_snapshot() -> dict[str, str | None]:
    names = [
        "TEST_KASPI_CLIENT_REQUEST_ID",
        "TEST_KASPI_IIN",
        "TEST_KASPI_SUM",
        "TEST_KASPI_CLIENT_REQUEST_PAYMENT_ID",
        "TEST_KASPI_PAYMENT_IIN",
        "TEST_KASPI_PAYMENT_SUM",
    ]
    return {name: os.getenv(name) for name in names}
