import hashlib
import re
from typing import Any
from xml.etree import ElementTree as ET


def make_flat_params_array(params: dict[str, Any], parent_name: str = "") -> dict[str, str]:
    """Port of PHP ``makeFlatParamsArray`` for Paybox ``pg_sig``."""
    flat: dict[str, str] = {}
    index = 0
    for key, value in params.items():
        index += 1
        name = f"{parent_name}{key}{index:03d}"
        if isinstance(value, dict):
            flat.update(make_flat_params_array(value, name))
            continue
        flat[name] = str(value)
    return flat


def paybox_signature(data: dict[str, Any], script_name: str, secret_key: str) -> str:
    flat = make_flat_params_array(data)
    parts = sorted(flat.values())
    parts.insert(0, script_name)
    parts.append(secret_key)
    return hashlib.md5(";".join(parts).encode()).hexdigest()


def parse_xml_response(raw: str, xpath_local_name: str) -> list[dict[str, Any]]:
    """Parse Forte/Paybox XML; strip ``ns:`` prefixes like legacy PHP."""
    cleaned = re.sub(r"(<\/?)(\w+):([^>]*>)", r"\1\2\3", raw)
    root = ET.fromstring(cleaned)
    matches: list[dict[str, Any]] = []
    for element in root.iter():
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag.lower() != xpath_local_name.lower():
            continue
        matches.append(_element_to_dict(element))
    return matches


def _element_to_dict(element: ET.Element) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for child in element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if len(child):
            value = _element_to_dict(child)
        else:
            value = child.text
        if tag in result:
            existing = result[tag]
            if not isinstance(existing, list):
                result[tag] = [existing]
            result[tag].append(value)
        else:
            result[tag] = value
    if element.text and element.text.strip() and not list(element):
        return {element.tag: element.text.strip()}
    return result
