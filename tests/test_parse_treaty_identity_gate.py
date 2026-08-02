import pytest

import parse_treaty
from taxtreat.parser.extractor import ExtractionResult
from taxtreat.parser.official_source import OfficialSourceError
from taxtreat.validation.document_identity import TreatyIdentityError


@pytest.fixture(autouse=True)
def _disable_real_official_source(monkeypatch):
    def unavailable(*args, **kwargs):
        raise OfficialSourceError("official source disabled in local identity tests")

    monkeypatch.setattr(parse_treaty, "fetch_official_document", unavailable)


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
        "extract_document",
        lambda path: ExtractionResult(_pages("Státem Izrael"), "test", 100),
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
        "extract_document",
        lambda path: ExtractionResult(_pages("Rakouskou republikou"), "test", 100),
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
    assert parsed.text_extraction["method"] == "test"
    assert parsed.source_resolution["status"] in {"fallback", "resolved"}

    output = tmp_path / "nested" / "austria.json"
    parse_treaty.write_parsed_treaty(parsed, output)

    saved = output.read_text(encoding="utf-8")
    assert '"identity_validation"' in saved
    assert '"validated"' in saved
