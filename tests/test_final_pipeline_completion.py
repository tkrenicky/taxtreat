from __future__ import annotations

import json
from pathlib import Path

import parse_treaty
from taxtreat.engine.extractors import dividend_rule
from taxtreat.parser.extractor import ExtractionResult, _extract_with_ocr
from taxtreat.parser.official_source import OfficialSourceDocument, official_source_urls
from taxtreat.tools import benchmark_treaties


def test_adaptive_ocr_continues_past_first_batch_until_expected_treaty(monkeypatch, tmp_path):
    pdf = tmp_path / "issue.pdf"
    pdf.write_bytes(b"%PDF-fake")
    calls: list[int] = []

    monkeypatch.setenv("TAXTREAT_OCR_MAX_PAGES", "20")
    monkeypatch.setenv("TAXTREAT_OCR_BATCH_PAGES", "20")
    monkeypatch.setenv("TAXTREAT_OCR_HARD_MAX_PAGES", "0")
    monkeypatch.setattr("taxtreat.parser.extractor.shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("taxtreat.parser.extractor._pdf_page_count", lambda path: 45)

    def fake_page(path, page_number, **kwargs):
        calls.append(page_number)
        if page_number == 1:
            return "Smlouva mezi Českou republikou a Izraelem\nČlánek 1\nČlánek 10\nČlánek 11\nČlánek 12"
        if page_number == 21:
            return "Smlouva mezi Českou republikou a Maďarskou republikou"
        if page_number == 22:
            return "Článek 1\nOsoby"
        if page_number == 30:
            return "Článek 10\nDividendy"
        if page_number == 31:
            return "Článek 11\nÚroky"
        if page_number == 32:
            return "Článek 12\nLicenční poplatky"
        return ""

    monkeypatch.setattr("taxtreat.parser.extractor._ocr_pdf_page", fake_page)

    pages = _extract_with_ocr(pdf, expected_country="Maďarsko")

    assert len(pages) == 40
    assert max(calls) == 40
    assert "Maďarskou" in pages[20]


def test_official_source_urls_are_derived_without_country_map():
    assert official_source_urls("483/2024 Sb.")[0] == (
        "https://e-sbirka.gov.cz/sb/2024/483/0000-00-00"
    )
    assert official_source_urls("89/2007 Sb.m.s.")[0] == (
        "https://e-sbirka.gov.cz/sm/2007/89/0000-00-00"
    )


def test_parser_falls_back_to_official_esbirka_text(monkeypatch):
    wrong = [
        "SMLOUVA mezi Českou republikou a jiným státem.\n"
        "Článek 1\nOsoby\nČlánek 10\nDividendy"
    ]
    official = """
    SDĚLENÍ Ministerstva zahraničních věcí
    Smlouva mezi Českou republikou a Rwandskou republikou.
    Článek 1
    OSOBY, NA KTERÉ SE SMLOUVA VZTAHUJE
    Text.
    Článek 10
    DIVIDENDY
    Daň nepřesáhne 10 procent hrubé částky dividend.
    Článek 11
    ÚROKY
    Text úroků.
    Článek 12
    LICENČNÍ POPLATKY
    Text licenčních poplatků.
    Článek 13
    ZISKY ZE ZCIZENÍ MAJETKU
    """ * 20

    monkeypatch.setattr(
        parse_treaty,
        "extract_document",
        lambda *args, **kwargs: ExtractionResult(wrong, "local", 10),
    )
    monkeypatch.setattr(
        parse_treaty,
        "fetch_official_document",
        lambda title: OfficialSourceDocument(
            pages=[official],
            url="https://e-sbirka.gov.cz/sb/2024/482/0000-00-00",
        ),
    )

    parsed = parse_treaty.parse_treaty_file(
        "broken.pdf",
        country="Rwanda",
        source_title="482/2024 Sb.",
    )

    assert parsed.text_extraction["method"] == "official_esbirka_html"
    assert parsed.source_resolution["method"] == "official_esbirka_html"
    assert {article.number for article in parsed.articles} >= {1, 10, 11, 12}


def test_czech_tax_rate_is_not_misclassified_as_ownership():
    rule = dividend_rule(
        "Jestliže skutečný vlastník dividend je rezidentem druhého státu, "
        "daň takto uložená nepřesáhne 10 procent hrubé částky dividend."
    )
    assert [rate.rate for rate in rule.rates] == [10.0]


def test_word_percentage_is_extracted():
    rule = dividend_rule(
        "Česká daň nepřesáhne pět procent hrubé částky dividend."
    )
    assert [rate.rate for rate in rule.rates] == [5.0]
