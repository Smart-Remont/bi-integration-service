"""Helpers for Payments unit tests."""

from __future__ import annotations

import xml.etree.ElementTree as ET


def parse_kaspi_xml(text: str) -> ET.Element:
    return ET.fromstring(text)


def kaspi_result(text: str) -> str:
    root = parse_kaspi_xml(text)
    el = root.find("result")
    assert el is not None and el.text is not None
    return el.text


def kaspi_txn_id(text: str) -> str:
    root = parse_kaspi_xml(text)
    el = root.find("txn_id")
    assert el is not None and el.text is not None
    return el.text
