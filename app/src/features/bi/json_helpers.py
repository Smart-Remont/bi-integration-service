"""Parsing helpers for legacy BI/CRM stored-function scalar results.

Several SPs in this domain (``bi_rakurs_list_v2``, ``read_preset_for_big_app``,
``bi_get_client_request_material_json``, ``sr_showroom_report``,
``sr_resident_report``) return a JSON-encoded *string* rather than ``jsonb`` —
legacy PHP does ``json_decode($row['value'])`` after fetching it. We mirror that.
"""

import json


def parse_scalar_json(value: object | None) -> object | None:
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value
