from pathlib import Path

import pytest

from taxtreat.tools.extract_at_treaty_article_candidates import (
    build_article_candidate_inventory,
    extract_article_blocks,
    extract_nonstandard_royalty_blocks,
)


TEXT = """
PREAMBLE
Artikel 10
DIVIDENDEN
1. Dividenden dürfen im anderen Staat besteuert werden. Der Quellenstaat darf jedoch ebenfalls besteuern, sofern die Voraussetzungen dieses Artikels erfüllt sind.
2. Ist der Nutzungsberechtigte im anderen Staat ansässig, darf die Steuer einen im Abkommen bestimmten Prozentsatz des Bruttobetrags nicht übersteigen.
Artikel 11
ZINSEN
1. Zinsen dürfen nur im anderen Staat besteuert werden, wenn der Nutzungsberechtigte dort ansässig ist und keine Betriebsstättenzurechnung vorliegt.
2. Bei besonderen Beziehungen zwischen Schuldner und Nutzungsberechtigtem gilt die Begünstigung nur für den fremdüblichen Betrag.
Artikel 12
LIZENZGEBÜHREN
1. Lizenzgebühren dürfen im anderen Staat besteuert werden, wenn der Nutzungsberechtigte dort ansässig ist und die Voraussetzungen dieses Artikels erfüllt sind.
2. Bei einer Betriebsstättenzurechnung gelten die Regeln des einschlägigen Unternehmensgewinnartikels anstelle dieses Artikels.
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


def test_nonstandard_royalty_scanner_finds_article_9_without_reclassifying_target_inventory():
    text = """
Artikel 8
Einkünfte aus unbeweglichem Vermögen werden hier geregelt. Weitere Bestimmungen folgen.
Artikel 9
Lizenzgebühren aus einem Vertragsstaat dürfen nur im anderen Staat besteuert werden. Der Ausdruck Lizenzgebühren umfasst Urheberrechte, Patente und Warenzeichen. Weitere Lizenzgebühren unterliegen derselben Bestimmung.
Artikel 10
Zinsen werden in diesem Artikel geregelt. Weitere Bestimmungen über Zinsen folgen hier.
"""
    semantic = extract_nonstandard_royalty_blocks(text)
    assert len(semantic) == 1
    assert semantic[0][0] == 9
    assert semantic[0][1].startswith("Artikel 9")
    assert set(extract_article_blocks(text)) == {10}


def test_candidate_inventory_hashes_substantive_text_without_releasing_rates(tmp_path: Path):
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
    assert result["schema_version"] == 4
    assert result["status"] == "article_text_candidates_not_reviewed"
    assert row["article_candidate_presence"] == {"10": 1, "11": 1, "12": 1}
    assert row["rejected_article_candidate_presence"] == {"10": 0, "11": 0, "12": 0}
    assert row["primary_text_review_completed"] is False
    assert row["rate_extraction_released"] is False
    candidates = row["sources"][0]["article_candidates"]
    assert {candidate["article_number"] for candidate in candidates} == {10, 11, 12}
    assert all(candidate["substantive_article_candidate"] is True for candidate in candidates)
    assert all(candidate["semantic_income_candidate"] is None for candidate in candidates)
    assert all(candidate["quality_flags"] == [] for candidate in candidates)
    assert all(len(candidate["text_sha256"]) == 64 for candidate in candidates)
    assert all(candidate["legal_review_completed"] is False for candidate in candidates)
    assert len(list((tmp_path / "articles").glob("*.txt"))) == 3


def test_candidate_inventory_retains_nonstandard_royalty_candidate_separately(tmp_path: Path):
    source = tmp_path / "old-treaty.html"
    source.write_text(
        "<pre>Artikel 9\nLizenzgebühren dürfen mit 10 Prozent besteuert werden. "
        "Der Ausdruck Lizenzgebühren umfasst Patente und Marken. Weitere Lizenzgebühren folgen.\n"
        "Artikel 10\nZinsen können besteuert werden. Weitere Regeln über Zinsen folgen.\n"
        "Artikel 11\nAndere Einkünfte werden geregelt. Weitere Regeln folgen.\n"
        "Artikel 12\nÖffentliche Vergütungen werden geregelt. Weitere Regeln folgen.\n"
        "Artikel 13\nEnde.</pre>",
        encoding="utf-8",
    )
    pilot = {
        "source_country": "AT",
        "status": "instrument_chain_pilot_acquired_not_reviewed",
        "partners": [{
            "partner_label": "Old / Old",
            "sources": [{
                "source_order": 1,
                "artifact_path": str(source),
                "content_type": "text/html",
                "final_url": "https://www.ris.bka.gv.at/old",
                "role_candidate": "published_instrument_or_protocol",
                "sha256": "c" * 64,
            }],
        }],
    }
    result = build_article_candidate_inventory(pilot, article_dir=tmp_path / "articles")
    candidates = result["partners"][0]["sources"][0]["article_candidates"]
    semantic = [c for c in candidates if c.get("semantic_income_candidate") == "royalty"]
    assert len(semantic) == 1
    assert semantic[0]["article_number"] == 9
    assert result["partners"][0]["article_candidate_presence"] == {"10": 0, "11": 0, "12": 0}


def test_cross_reference_only_article_heading_is_retained_but_not_counted_as_substantive(tmp_path: Path):
    source = tmp_path / "protocol.html"
    source.write_text(
        "<pre>Artikel 10\nArtikel 10 Absatz 2 des Abkommens wird ersetzt.\n"
        "Artikel 11\nArtikel 11 bleibt unverändert.\n"
        "Artikel 12\nArtikel 12 Absatz 1 wird wie folgt geändert.\nArtikel 13\nEnde.</pre>",
        encoding="utf-8",
    )
    pilot = {
        "source_country": "AT",
        "status": "instrument_chain_pilot_acquired_not_reviewed",
        "partners": [{
            "partner_label": "Protocol / Protocol",
            "sources": [{
                "source_order": 1,
                "artifact_path": str(source),
                "content_type": "text/html",
                "final_url": "https://www.ris.bka.gv.at/protocol",
                "role_candidate": "current_consolidated_view",
                "sha256": "b" * 64,
            }],
        }],
    }

    result = build_article_candidate_inventory(pilot, article_dir=tmp_path / "articles")
    row = result["partners"][0]
    assert row["article_candidate_presence"] == {"10": 0, "11": 0, "12": 0}
    assert row["rejected_article_candidate_presence"] == {"10": 1, "11": 1, "12": 1}
    assert all(candidate["substantive_article_candidate"] is False for candidate in row["sources"][0]["article_candidates"])


def test_candidate_inventory_fails_closed_on_missing_acquired_source(tmp_path: Path):
    pilot = {
        "source_country": "AT",
        "status": "instrument_chain_pilot_acquired_not_reviewed",
        "partners": [{
            "partner_label": "Example / Example",
            "sources": [{
                "artifact_path": str(tmp_path / "missing.pdf"),
                "content_type": "application/pdf",
            }],
        }],
    }
    with pytest.raises(ValueError, match="Missing acquired treaty source"):
        build_article_candidate_inventory(pilot, article_dir=tmp_path / "articles")
