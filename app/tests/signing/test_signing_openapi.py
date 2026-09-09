"""OpenAPI: MyNCA callbacks show JSON body + ack responses in Scalar/Swagger."""

from __future__ import annotations

from src.main import app


def test_mynca_callback_openapi_has_json_body_and_acks() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    for route in (
        "/api/signing/callbacks/client-sign",
        "/api/signing/callbacks/project-remont",
        "/api/signing/callbacks/app",
        "/api/signing/callbacks/defect",
    ):
        post = paths[route]["post"]
        body = post["requestBody"]["content"]["application/json"]
        assert "example" in body
        assert post["responses"]["200"]["content"]["application/json"]["example"] == {"status": True}
        assert "400" in post["responses"]
        assert "500" in post["responses"]


def test_third_party_sign_back_openapi_is_form() -> None:
    post = app.openapi()["paths"]["/api/signing/third-party-app-sign-back"]["post"]
    form = post["requestBody"]["content"]["application/x-www-form-urlencoded"]
    assert "id" in form["schema"]["properties"]
    assert "signed_xml" in form["schema"]["properties"]
