from pathlib import Path

import pytest

from taxtreat.tools.extract_at_treaty_article_candidates import (
    build_article_candidate_inventory,
    extract_article_blocks,
)


TEXT = """
PREAMBLE
Artikel 10
DIVIDENDEN
1. Dividenden dürfen im anderen Staat besteuert werden.
2. Die Steuer darf zehn Prozent nicht übersteigen.
Artikel 11
ZINSEN
1. Zinsen dürfen nur im anderen Staat besteuert werden.
Artikel 12
LIZENZGEBÜHREN
1. Lizenzgebühren dürfen im anderen Staat besteuert werden.
Artikel 13
GEWINNE AUS DER VERÄUSSERUNG VON VERMÖGEN
1. Folgetext.
"""


def test_article_block_extractor_separates_10_11_12_at_next_article_heading():
    blocks = extract_article_blocks(TEXT)

    assert set(blocks) == {10, 11, 12}
    assert blocks[10].startswith("Artikel 10")
    assert "Artikel 11" not in blocks[10]
    assert blocks[11].startswith("Artikel 11")
    assert "Artikel 12" not in blocks[11]
    assert blocks[12].startswith("Artikel 12")
    assert "Artikel 13" not in blocks[12]


def test_article_block_extractor_accepts_english_and_art_abbreviation():
    blocks = extract_article_blocks(
        "Article 10\nDividends and enough substantive treaty text here.\n"
        "Art. 11\nInterest and enough substantive treaty text here.\n"
        "ARTICLE 12\nRoyalties and enough substantive treaty text here.\n"
        "Article 13\nNext article and enough text."
    )
    assert set(blocks) == {10, 11, 12}


def test_candidate_inventory_hashes_text_without_releasing_rates(tmp_path: Path):
    source = tmp_path / "treaty.html"
    source.write_text(f"<html><body><pre>{TEXT}</pre></body></html>", encoding="utf-8")
    pilot = {
        "source_country": "AT",
        "status": "instrument_chain_pilot_acquired_not_reviewed",
        "partners": [
            {
                "partner_label": "Example / Example",
                "sources": [
                    {
                        "source_order": 1,
                        "artifact_path": str(source),
                        "content_type": "text/html",
                        "final_url": "https://www.ris.bka.gv.at/example",
                        "role_candidate": "current_consolidated_view",
                        "sha256": "a" * 64,
                    }
                ],
            }
        ],
    }

    result = build_article_candidate_inventory(pilot, article_dir=tmp_path / "articles")
    row = result["partners"][0]
    assert result["status"] == "article_text_candidates_not_reviewed"
    assert row["article_candidate_presence"] == {"10": 1, "11": 1, "12": 1}
    assert row["primary_text_review_completed"] is False
    assert row["rate_extraction_released"] is False
    candidates = row["sources"][0]["article_candidates"]
    assert {candidate["article_number"] for candidate in candidates} == {10, 11, 12}
    assert all(len(candidate["text_sha256"]) == 64 for candidate in candidates)
    assert all(candidate["legal_review_completed"] is False for candidate in candidates)
    assert len(list((tmp_path / "articles").glob("*.txt"))) == 3


def test_candidate_inventory_fails_closed_on_missing_acquired_source(tmp_path: Path):
    pilot = {
        "source_country": "AT",
        "status": "instrument_chain_pilot_acquired_not_reviewed",
        "partners": [
            {
                "partner_label": "Example / Example",
                "sources": [
                    {
                        "artifact_path": str(tmp_path / "missing.pdf"),
                        "content_type": "application/pdf",
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValueError, match="Missing acquired treaty source"):
        build_article_candidate_inventory(pilot, article_dir=tmp_path / "articles")
