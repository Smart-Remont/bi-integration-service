"""Parse X509 certificate from Aitu signed XML — port of ``parseX509Sign()`` in CommonFunc.php."""

from __future__ import annotations

import re
import subprocess
import tempfile
from typing import Any
from xml.etree import ElementTree as ET


def parse_x509_sign(signed_xml: str) -> dict[str, Any]:
    try:
        root = ET.fromstring(signed_xml)
        ns = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
        cert_nodes = root.findall(".//ds:X509Certificate", ns)
        if not cert_nodes:
            cert_nodes = root.findall(".//{http://www.w3.org/2000/09/xmldsig#}X509Certificate")
        if not cert_nodes or cert_nodes[0].text is None:
            raise ValueError("X509Certificate not found in signed XML")

        cert_body = cert_nodes[0].text.strip()
        pem = f"-----BEGIN CERTIFICATE-----\n{cert_body}\n-----END CERTIFICATE-----"
        dn_name = _openssl_subject_dn(pem)

        return {
            "status": True,
            "dn_name": dn_name,
            "signed_xml": signed_xml,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": False, "error": str(exc)}


def _openssl_subject_dn(pem: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=True) as tmp:
        tmp.write(pem)
        tmp.flush()
        proc = subprocess.run(
            ["openssl", "x509", "-noout", "-subject", "-in", tmp.name],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "openssl x509 failed")
        subject = proc.stdout.strip()
        # Legacy PHP: json_encode subject keys → strip braces/quotes, comma spacing, colon→=
        subject = re.sub(r"^subject=\s*", "", subject)
        subject = subject.replace("/", ", ")
        subject = subject.replace("=", "=")
        return subject
