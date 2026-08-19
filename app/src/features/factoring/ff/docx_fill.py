"""Fill Freedom factoring DOCX templates.

Bank templates use ``{{placeholder}}``; Word often splits them across ``w:t`` runs.
We join text per paragraph, replace, then put the result into the first run.
"""

from __future__ import annotations

import io
import re
import zipfile
from xml.sax.saxutils import escape, unescape

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(.*?)\s*\}\}", re.DOTALL)
_WT_RE = re.compile(r"(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)", re.DOTALL)
_WP_RE = re.compile(r"<w:p\b[\s\S]*?</w:p>")
_STATIC_CONTRACT = "{номер договора ЮД статично}"

_ALIASES = {
    "borrower full_name": "borrower_full_name",
    "borrower.otp": "borrower_otp",
    "total amount": "total_amount",
}


def fill_docx_bytes(docx_bytes: bytes, values: dict[str, str]) -> bytes:
    source = zipfile.ZipFile(io.BytesIO(docx_bytes))
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as dest:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                data = _fill_xml(data, values)
            dest.writestr(item, data)
    return output.getvalue()


def replace_placeholders(text: str, values: dict[str, str]) -> str:
    def _repl(match: re.Match[str]) -> str:
        raw = re.sub(r"\s+", " ", match.group(1)).strip()
        key = _ALIASES.get(raw, raw.replace(" ", "_").replace(".", "_"))
        if key in values:
            return values[key]
        return match.group(0)

    result = _PLACEHOLDER_RE.sub(_repl, text)
    contract = values.get("contract_number")
    if contract and _STATIC_CONTRACT in result:
        result = result.replace(_STATIC_CONTRACT, contract)
    return result


def _fill_xml(xml: bytes, values: dict[str, str]) -> bytes:
    text = xml.decode("utf-8")

    def _fill_paragraph(match: re.Match[str]) -> str:
        paragraph = match.group(0)
        texts = [_xml_text(inner) for _, inner, _ in _WT_RE.findall(paragraph)]
        if not texts:
            return paragraph
        joined = "".join(texts)
        replaced = replace_placeholders(joined, values)
        if replaced == joined:
            return paragraph
        first = True

        def _put_text(wt_match: re.Match[str]) -> str:
            nonlocal first
            body = escape(replaced) if first else ""
            first = False
            return f"{wt_match.group(1)}{body}{wt_match.group(3)}"

        return _WT_RE.sub(_put_text, paragraph)

    return _WP_RE.sub(_fill_paragraph, text).encode("utf-8")


def _xml_text(fragment: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", fragment))
