from __future__ import annotations

import html
import re
from typing import Any


def sanitize_lead_value(value: Any) -> Any:
    if isinstance(value, str):
        cleaned = re.sub(r"\s+", " ", value).strip()
        return html.escape(cleaned, quote=True)
    return value


def sanitize_lead_tree(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: sanitize_lead_tree(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_lead_tree(v) for v in payload]
    return sanitize_lead_value(payload)
