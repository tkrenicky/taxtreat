from __future__ import annotations

from dataclasses import dataclass

from scripts.recover_esbirka_legal_pdfs import (
    is_pdf_response,
    legally_binding_complete_url,
    legacy_verified_url,
)


@dataclass
class DummyResponse:
    status_code: int
    content: bytes


def test_legally_binding_complete_url_uses_document_id_path_only() -> None:
    assert legally_binding_complete_url(390641) == (
        "https://e-sbirka.gov.cz/sbr-externi/stahni/"
        "pravne-zavazne-zneni-vcetne-uplnych/390641"
    )


def test_legacy_verified_url_uses_document_id_path_only() -> None:
    assert legacy_verified_url(224063).endswith("/stahni/overena-zneni/224063")


def test_pdf_detection_is_fail_closed() -> None:
    assert is_pdf_response(DummyResponse(200, b"%PDF-1.7\nbody"))
    assert not is_pdf_response(DummyResponse(200, b"<html>not a pdf</html>"))
    assert not is_pdf_response(DummyResponse(400, b"%PDF-1.7\nbody"))
