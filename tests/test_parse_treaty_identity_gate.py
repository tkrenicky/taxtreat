import pytest

import parse_treaty
from taxtreat.validation.document_identity import TreatyIdentityError


def _pages(counterparty: str) -> list[str]:
    return [
        (
            "SMLOUVA mezi Českou republikou a "
            f"{counterparty} o zamezení dvojímu zdanění. "
            "Tato smlouva upravuje zdanění příjmů a majetku smluvních států.\n"
            "Článek 1\nOsoby, na které se smlouva vztahuje.\n"
            "Článek 2\nDaně, na které se smlouva vztahuje."
        ),
        (
            "Článek 10\nDividendy\n"
            "1. Dividendy vyplácené společností mohou být zdaněny."
        ),
    ]


def test_parser_rejects_wrong_counterparty_before_article_detection(monkeypatch):
    monkeypatch.setattr(
        parse_treaty,
        "extract_pdf_pages",
        lambda path: _pages("Státem Izrael"),
    )

    with pytest.raises(TreatyIdentityError) as exc_info:
        parse_treaty.parse_treaty_file(
            "wrong.pdf",
            country="Maďarsko",
            source_title="21/1995 Sb.",
        )

    assert exc_info.value.result.reason == "counterparty_not_found"
    assert "Maďarsko" in str(exc_info.value)


def test_parser_records_validated_identity_in_normalized_json(monkeypatch, tmp_path):
    monkeypatch.setattr(
        parse_treaty,
        "extract_pdf_pages",
        lambda path: _pages("Rakouskou republikou"),
    )

    parsed = parse_treaty.parse_treaty_file(
        "austria.pdf",
        country="Rakousko",
        source_title="48/2007 Sb.m.s.",
    )

    assert parsed.identity_validation is not None
    assert parsed.identity_validation["status"] == "validated"
    assert parsed.identity_validation["expected_country"] == "Rakousko"
    assert parsed.articles

    output = tmp_path / "nested" / "austria.json"
    parse_treaty.write_parsed_treaty(parsed, output)

    saved = output.read_text(encoding="utf-8")
    assert '"identity_validation"' in saved
    assert '"validated"' in saved


def test_parser_selects_matching_treaty_from_multi_treaty_publication(monkeypatch):
    pages = [
        (
            "Sbírka zákonů č. 21 / 1995. "
            "SMLOUVA mezi Českou republikou a Státem Izrael.\n"
            "Článek 1\nOsoby.\nČlánek 2\nDaně."
        ),
        "Článek 10\nDividendy\n1. Izraelská sazba 15 %.",
        (
            "Sbírka zákonů č. 22 / 1995. "
            "SMLOUVA mezi Českou republikou a Maďarskou republikou.\n"
            "Článek 1\nOsoby.\nČlánek 2\nDaně."
        ),
        "Článek 10\nDividendy\n1. Maďarská sazba 10 %.",
    ]
    monkeypatch.setattr(parse_treaty, "extract_pdf_pages", lambda path: pages)

    parsed = parse_treaty.parse_treaty_file(
        "collection.pdf",
        country="Maďarsko",
        source_title="22/1995 Sb.",
    )

    assert parsed.start_page == 3
    article10 = next(article for article in parsed.articles if article.number == 10)
    assert "Maďarská sazba" in article10.text
    assert "Izraelská sazba" not in article10.text
    assert parsed.identity_validation["publication_reference_found"] is True


def test_parser_rejects_country_match_with_wrong_notice_number_in_collection(monkeypatch):
    pages = [
        (
            "Sbírka zákonů č. 21 / 1995. "
            "SMLOUVA mezi Českou republikou a Státem Izrael.\n"
            "Článek 1\nOsoby.\nČlánek 2\nDaně."
        ),
        "Článek 10\nDividendy\n1. Izraelská sazba 15 %.",
        (
            "Sbírka zákonů č. 22 / 1995. "
            "SMLOUVA mezi Českou republikou a Maďarskou republikou.\n"
            "Článek 1\nOsoby.\nČlánek 2\nDaně."
        ),
        "Článek 10\nDividendy\n1. Maďarská sazba 10 %.",
    ]
    monkeypatch.setattr(parse_treaty, "extract_pdf_pages", lambda path: pages)

    with pytest.raises(TreatyIdentityError) as exc_info:
        parse_treaty.parse_treaty_file(
            "collection.pdf",
            country="Maďarsko",
            source_title="21/1995 Sb.",
        )

    assert exc_info.value.result.reason == "publication_reference_mismatch"


def test_parser_preserves_insufficient_text_identity_rejection(monkeypatch):
    monkeypatch.setattr(parse_treaty, "extract_pdf_pages", lambda path: [""])

    with pytest.raises(TreatyIdentityError) as exc_info:
        parse_treaty.parse_treaty_file(
            "scan.pdf",
            country="Itálie",
            source_title="17/1985 Sb.",
        )

    assert exc_info.value.result.reason == "insufficient_text"


def test_parser_reports_detector_failure_after_document_identity_passes(monkeypatch):
    monkeypatch.setattr(
        parse_treaty,
        "extract_pdf_pages",
        lambda path: [
            "Smlouva s Rakouskou republikou o zamezení dvojímu zdanění. "
            "Dokument obsahuje dostatek textu, ale nadpis článku jedna není "
            "v tomto testovacím vstupu rozpoznatelný strukturálním detektorem."
        ],
    )

    with pytest.raises(RuntimeError, match="Treaty start not found"):
        parse_treaty.parse_treaty_file(
            "undetected.pdf",
            country="Rakousko",
            source_title="48/2007 Sb.m.s.",
        )
