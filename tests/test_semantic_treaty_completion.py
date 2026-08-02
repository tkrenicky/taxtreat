from __future__ import annotations

import json
from pathlib import Path

from taxtreat.parser.article_selection import (
    article_type,
    select_best_article_sequence,
)
from taxtreat.parser.extractor import ExtractionResult, _ocr_target_reached
from taxtreat.parser.models import TreatyArticle
from taxtreat.parser.official_source import fetch_official_document
from taxtreat.parser.publication import select_treaty_pages
from taxtreat.tools.benchmark_treaties import benchmark


def _article(number: int, title: str, text: str = "Text.") -> TreatyArticle:
    return TreatyArticle(number=number, title=title, text=text)


def test_best_sequence_ignores_unrelated_legal_act_with_same_article_numbers():
    unrelated = [
        _article(1, "Účel smlouvy"),
        _article(10, "Doručování písemností"),
        _article(11, "Náklady řízení"),
        _article(12, "Závěrečná ustanovení"),
    ]
    treaty = [
        _article(1, "OSOBY, NA KTERÉ SE SMLOUVA VZTAHUJE"),
        _article(9, "DIVIDENDY", "Daň nepřesáhne 10 procent hrubé částky dividend."),
        _article(10, "PŘÍJMY Z POHLEDÁVEK"),
        _article(11, "LICENČNÍ POPLATKY"),
    ]

    selected = select_best_article_sequence(unrelated + treaty)

    assert selected.is_complete is True
    assert {name: article.number for name, article in selected.semantic_articles.items()} == {
        "dividend": 9,
        "interest": 10,
        "royalty": 11,
    }
    assert selected.articles == treaty


def test_benchmark_uses_semantic_articles_instead_of_fixed_oecd_numbers(tmp_path: Path):
    payload = {
        "identity_validation": {"status": "validated", "reason": "counterparty_matched"},
        "text_extraction": {"method": "pypdf", "score": 100},
        "source_resolution": {"status": "resolved", "method": "notice_country_match"},
        "articles": [
            {"number": 1, "title": "OSOBY", "text": "Text."},
            {
                "number": 9,
                "title": "DIVIDENDY",
                "text": "Daň nepřesáhne 10 procent hrubé částky dividend.",
            },
            {"number": 10, "title": "PŘÍJMY Z POHLEDÁVEK", "text": "Text."},
            {"number": 11, "title": "LICENČNÍ POPLATKY", "text": "Text."},
        ],
    }
    path = tmp_path / "nonstandard.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    result = benchmark(path)

    assert result["dividend_article_number"] == 9
    assert result["interest_article_number"] == 10
    assert result["royalty_article_number"] == 11
    assert result["dividend_rates"] == "10.0"


def test_ocr_damaged_article_11_heading_is_recovered_from_article_10_body():
    articles = [
        _article(
            10,
            "DIVIDENDY",
            "Text dividend.\nČlánek al\nÚroky\nText úroků.",
        ),
        _article(12, "LICENČNÍ POPLATKY", "Text licencí."),
    ]

    selected = select_best_article_sequence(articles)

    assert selected.is_complete is True
    assert selected.semantic_articles["interest"].number == 11
    assert article_type(selected.semantic_articles["interest"]) == "interest"


def test_ocr_stop_requires_one_semantically_complete_treaty_sequence():
    unrelated = [
        "Článek 1\nÚčel dohody",
        "Článek 10\nDoručování",
        "Článek 11\nNáklady",
        "Článek 12\nPlatnost",
    ]
    treaty = [
        "Článek 1\nOsoby",
        "Článek 10\nDIVIDENDY",
        "Článek 11\nÚROKY",
        "Článek 12\nLICENČNÍ POPLATKY",
    ]

    assert _ocr_target_reached(unrelated, None) is False
    assert _ocr_target_reached(unrelated + treaty, None) is True


def test_mojibake_notice_selects_tajik_treaty_and_corrects_publication_number():
    jordan = (
        "49 88 SDEÏ L E N IÂ Ministerstva zahranicÏnõÂch veÏcõÂ. "
        "Smlouva mezi CÏeskou republikou a JordaÂnskyÂm kraÂlovstvõÂm."
    )
    tajik = (
        "49 89 SDEÏ L E N IÂ Ministerstva zahranicÏnõÂch veÏcõÂ. "
        "Smlouva mezi CÏeskou republikou a TaÂdzÏickou republikou."
    )

    selected = select_treaty_pages(
        [jordan, "Článek 1\nJordan", tajik, "Článek 1\nTajik", "Článek 10\nDIVIDENDY"],
        expected_country="Tádžikistán",
        source_title="88/2007 Sb.m.s.",
    )

    assert selected.status == "resolved"
    assert selected.start_page == 3
    assert selected.effective_title == "89/2007 Sb.m.s."
    assert selected.metadata_mismatch is True


def test_official_source_follows_linked_pdf(monkeypatch):
    html = b'<html><main><a href="/files/treaty.pdf">Stahnout PDF</a></main></html>'
    pdf = b"%PDF-1.7 fake"

    class Headers:
        def __init__(self, content_type: str):
            self.content_type = content_type

        def get_content_type(self):
            return self.content_type

    class Response:
        def __init__(self, payload: bytes, content_type: str):
            self.payload = payload
            self.headers = Headers(content_type)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.payload

    def fake_urlopen(request, timeout):
        url = request.full_url
        if url.endswith("treaty.pdf"):
            return Response(pdf, "application/pdf")
        return Response(html, "text/html")

    treaty_pages = [
        "Smlouva mezi Českou republikou a Rwandskou republikou o zamezení dvojímu zdanění.\n"
        "Článek 1\nOSOBY\n"
        "Článek 10\nDIVIDENDY\nDaň nepřesáhne 10 procent.\n"
        "Článek 11\nÚROKY\nText.\n"
        "Článek 12\nLICENČNÍ POPLATKY\nText.\n"
        "Článek 13\nZISKY ZE ZCIZENÍ MAJETKU"
    ]

    monkeypatch.setattr("taxtreat.parser.official_source.urlopen", fake_urlopen)
    monkeypatch.setattr(
        "taxtreat.parser.extractor.extract_document",
        lambda *args, **kwargs: ExtractionResult(treaty_pages, "ocr", 100),
    )

    result = fetch_official_document(
        "482/2024 Sb.",
        expected_country="Rwanda",
        timeout=1,
    )

    assert result.url == "https://e-sbirka.gov.cz/files/treaty.pdf"
    assert result.pages == treaty_pages
