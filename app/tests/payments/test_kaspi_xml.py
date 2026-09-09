"""Unit tests: Kaspi XML builders."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from src.features.payments.kaspi.xml import (
    check_success_xml,
    error_xml,
    info_fields,
    pay_success_xml,
)

from tests.payments.helpers import kaspi_result, kaspi_txn_id, parse_kaspi_xml


def test_error_xml_with_comment() -> None:
    xml = error_xml("TX-1", 5, "Something wrong")
    assert kaspi_txn_id(xml) == "TX-1"
    assert kaspi_result(xml) == "5"
    root = parse_kaspi_xml(xml)
    comment = root.find("comment")
    assert comment is not None
    assert comment.text == "Something wrong"
    assert xml.startswith("<?xml")


def test_error_xml_without_txn_id() -> None:
    xml = error_xml(None, 403, "Forbidden")
    root = parse_kaspi_xml(xml)
    assert root.find("txn_id") is None
    assert kaspi_result(xml) == "403"


def test_check_success_xml_strips_float_decimal_from_sum() -> None:
    xml = check_success_xml(
        txn_id="TX-F",
        result_code=0,
        company_bin="123456789012",
        fields=[],
        payment_amount=787088.0,
    )
    root = parse_kaspi_xml(xml)
    assert root.find("sum").text == "787088"  # type: ignore[union-attr]


def test_check_success_xml_fields_and_bin() -> None:
    fields = [
        ("field1", "ФИО", "Test User"),
        ("field2", "Номер договора", "99"),
    ]
    xml = check_success_xml(
        txn_id="TX-2",
        result_code=0,
        company_bin="123456789012",
        fields=fields,
        payment_amount="1500",
    )
    root = parse_kaspi_xml(xml)
    assert root.find("sum") is not None
    assert root.find("sum").text == "1500"  # type: ignore[union-attr]
    assert root.find("bin").text == "123456789012"  # type: ignore[union-attr]
    fields_el = root.find("fields")
    assert fields_el is not None
    children = list(fields_el)
    assert len(children) == 2
    assert children[0].tag == "field1"
    assert children[0].get("name") == "ФИО"
    assert children[0].text == "Test User"


def test_pay_success_xml_prv_txn() -> None:
    xml = pay_success_xml(
        txn_id="TX-3",
        prv_txn=77324,
        sum_value=1000,
        result_code=0,
        company_bin="251240017509",
    )
    root = parse_kaspi_xml(xml)
    assert root.find("prv_txn").text == "77324"  # type: ignore[union-attr]
    assert root.find("sum").text == "1000"  # type: ignore[union-attr]
    assert kaspi_result(xml) == "0"
    comment = root.find("comment")
    assert comment is not None and comment.text == "OK"


def test_info_fields_maps_sp_row() -> None:
    fields = info_fields(
        {
            "prop_fio": "A",
            "prop_number": "B",
            "prop_date": "C",
            "resident_name": "D",
            "company_name_official": "E",
        },
    )
    assert fields[0] == ("field1", "ФИО", "A")
    assert fields[4] == ("field5", "Название компании", "E")
