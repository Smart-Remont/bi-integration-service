from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def _indent(elem: ET.Element, level: int = 0) -> None:
    indent = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        for child in elem:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():  # noqa: PLW2901
            child.tail = indent
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = indent


def error_xml(
    txn_id: str | None,
    code: int | str,
    error: str | None = None,
) -> str:
    root = ET.Element("response")
    if txn_id is not None:
        ET.SubElement(root, "txn_id").text = str(txn_id)
    ET.SubElement(root, "result").text = str(code)
    if error is not None:
        ET.SubElement(root, "comment").text = str(error)
    _indent(root)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def check_success_xml(
    *,
    txn_id: str,
    result_code: int | str,
    company_bin: str,
    fields: list[tuple[str, str, str]],
    payment_amount: str | None = None,
) -> str:
    root = ET.Element("response")
    ET.SubElement(root, "txn_id").text = str(txn_id)
    ET.SubElement(root, "result").text = str(result_code)
    if payment_amount is not None:
        ET.SubElement(root, "sum").text = str(payment_amount)
    ET.SubElement(root, "bin").text = company_bin
    fields_el = ET.SubElement(root, "fields")
    for tag, name, value in fields:
        field_el = ET.SubElement(fields_el, tag)
        field_el.set("name", name)
        field_el.text = value
    ET.SubElement(root, "comment").text = ""
    _indent(root)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def pay_success_xml(
    *,
    txn_id: str,
    prv_txn: object,
    sum_value: object,
    result_code: int | str,
    company_bin: str,
) -> str:
    root = ET.Element("response")
    ET.SubElement(root, "txn_id").text = str(txn_id)
    ET.SubElement(root, "prv_txn").text = str(prv_txn)
    ET.SubElement(root, "sum").text = str(sum_value)
    ET.SubElement(root, "result").text = str(result_code)
    ET.SubElement(root, "bin").text = company_bin
    ET.SubElement(root, "comment").text = "OK"
    _indent(root)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def info_fields(info: dict[str, Any]) -> list[tuple[str, str, str]]:
    return [
        ("field1", "ФИО", str(info.get("prop_fio") or "")),
        ("field2", "Номер договора", str(info.get("prop_number") or "")),
        ("field3", "Дата договора", str(info.get("prop_date") or "")),
        ("field4", "ЖК", str(info.get("resident_name") or "")),
        ("field5", "Название компании", str(info.get("company_name_official") or "")),
    ]
