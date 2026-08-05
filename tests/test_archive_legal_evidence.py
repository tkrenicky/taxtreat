from __future__ import annotations

import hashlib

from taxtreat.tools import archive_legal_evidence as archive


def test_domain_allowlist_accepts_only_expected_official_domains() -> None:
    assert archive._domain_allowed(
        "https://mf.gov.cz/example.pdf"
    )
    assert archive._domain_allowed(
        "https://eur-lex.europa.eu/example"
    )
    assert archive._domain_allowed(
        "https://www.oecd.org/example.pdf"
    )

    assert not archive._domain_allowed(
        "https://example.com/document.pdf"
    )
    assert not archive._domain_allowed(
        "https://mf.gov.cz.example.com/document.pdf"
    )


def test_content_classification() -> None:
    assert archive._classify(
        b"%PDF-1.7 test",
        "application/octet-stream",
    ) == "pdf"

    assert archive._classify(
        b"<!doctype html><html></html>",
        "text/html",
    ) == "html"

    assert archive._classify(
        b"plain text",
        "text/plain",
    ) == "other"


def test_pdf_hash_is_stable() -> None:
    content = b"%PDF-1.7\nTaxTreat test\n"

    assert hashlib.sha256(content).hexdigest() == (
        "3e9d99605b1352cd2c3f65ad26f663d0"
        "7b737bfb5552a276cc536078bb6996d0"
    )


def test_e_sbirka_html_shell_is_not_accepted_as_evidence() -> None:
    assert archive._html_can_be_archived(
        "https://e-sbirka.gov.cz/sb/2024/439?zalozka=text"
    ) is False


def test_authoritative_html_sources_may_be_archived() -> None:
    assert archive._html_can_be_archived(
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/"
    )
    assert archive._html_can_be_archived(
        "https://mf.gov.cz/cs/example"
    )
    assert archive._html_can_be_archived(
        "https://opendata.eselpoint.gov.cz/example"
    )


def test_download_urls_are_derived_from_e_sbirka_page_url() -> None:
    source = {
        "metadata": {},
        "official_urls": [
            "https://e-sbirka.gov.cz/sb/2024/439?zalozka=text"
        ],
    }

    urls = archive._candidate_urls(source)

    assert urls[0] == (
        "https://e-sbirka.gov.cz/"
        "sb/2024/439/0000-00-00.PDF"
    )
    assert (
        "https://e-sbirka.gov.cz/"
        "sb/2024/439/0000-00-00.XML"
    ) in urls
    assert source["official_urls"][0] in urls
