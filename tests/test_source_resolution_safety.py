from pathlib import Path
from types import SimpleNamespace

import pytest

import parse_treaty
from taxtreat.parser.extractor import ExtractionResult
from taxtreat.parser.models import TreatyArticle
from taxtreat.parser.publication import PublicationSelection


def test_whole_document_fallback_rejects_multiple_treaty_sequences(monkeypatch):
    selection = PublicationSelection(
        pages=["Document mentioning Rusko"],
        status="fallback",
        method="whole_document",
        start_page=1,
        end_page=1,
        effective_title="1/2000 Sb.",
        metadata_mismatch=False,
        candidate_count=0,
    )

    monkeypatch.setattr(
        parse_treaty,
        "select_treaty_pages",
        lambda *args, **kwargs: selection,
    )
    monkeypatch.setattr(
        parse_treaty,
        "validate_treaty_identity",
        lambda **kwargs: SimpleNamespace(
            is_valid=kwargs.get("text") == "Document mentioning Rusko",
            to_dict=lambda: {"status": "validated"},
        ),
    )
    monkeypatch.setattr(
        parse_treaty,
        "extract_treaty",
        lambda pages: ("treaty text", 1),
    )
    monkeypatch.setattr(parse_treaty, "parse_articles", lambda text: [])
    monkeypatch.setattr(
        parse_treaty,
        "select_best_article_sequence",
        lambda articles: SimpleNamespace(
            articles=[],
            sequence_index=0,
            sequence_count=2,
            semantic_score=3,
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Ambiguous multi-treaty publication",
    ):
        parse_treaty._parse_extraction(
            ExtractionResult(["page"], "test", 100),
            source_path=Path("publication.pdf"),
            country="Rusko",
            source_title="1/2000 Sb.",
        )


@pytest.mark.parametrize("sequence_count", [1, 2])
def test_whole_document_fallback_accepts_validated_selected_sequence(
    monkeypatch,
    sequence_count,
):
    selection = PublicationSelection(
        pages=["Document mentioning Rusko"],
        status="fallback",
        method="whole_document",
        start_page=1,
        end_page=1,
        effective_title="1/2000 Sb.",
        metadata_mismatch=False,
        candidate_count=0,
    )
    article = TreatyArticle(
        number=10,
        title="DIVIDENDY",
        text="Smlouva mezi Českou republikou a Ruskem.",
        paragraphs=[],
    )

    monkeypatch.setattr(
        parse_treaty,
        "select_treaty_pages",
        lambda *args, **kwargs: selection,
    )
    monkeypatch.setattr(
        parse_treaty,
        "validate_treaty_identity",
        lambda **kwargs: SimpleNamespace(
            is_valid="Rus" in kwargs.get("text", ""),
            to_dict=lambda: {"status": "validated"},
        ),
    )
    monkeypatch.setattr(
        parse_treaty,
        "extract_treaty",
        lambda pages: ("treaty text", 1),
    )
    monkeypatch.setattr(parse_treaty, "parse_articles", lambda text: [article])
    monkeypatch.setattr(
        parse_treaty,
        "select_best_article_sequence",
        lambda articles: SimpleNamespace(
            articles=[article],
            sequence_index=1,
            sequence_count=sequence_count,
            semantic_score=3,
        ),
    )

    parsed = parse_treaty._parse_extraction(
        ExtractionResult(["page"], "test", 100),
        source_path=Path("publication.pdf"),
        country="Rusko",
        source_title="1/2000 Sb.",
    )

    assert parsed.source_resolution["status"] == "resolved"
    assert parsed.source_resolution["method"] == "validated_article_sequence"
    assert parsed.articles == [article]
