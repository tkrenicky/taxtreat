from pathlib import Path

from taxtreat.tools.build_at_language_evidence import build_language_evidence


def _fixture(tmp_path: Path):
    landing = tmp_path / "landing.html"
    landing.write_text(
        '<html><body>'
        '<a href="https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/deutsch.pdf" '
        'title="Signiertes PDF-Dokument: deutscher Vertragstext"></a>'
        '<a href="https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/english.pdf" '
        'title="Signiertes PDF-Dokument: englischer Vertragstext"></a>'
        '</body></html>',
        encoding="utf-8",
    )
    german = tmp_path / "de.pdf"
    german.write_bytes(b"german")
    english = tmp_path / "en.pdf"
    english.write_bytes(b"english")
    current = tmp_path / "current.html"
    current.write_text("Artikel 12 Lizenzgebuehren", encoding="utf-8")

    partners = []
    article_partners = []
    for index in range(89):
        label = f"Partner {index}"
        if index == 0:
            sources = [
                {
                    "source_order": 1,
                    "final_url": "https://www.ris.bka.gv.at/eli/bgbl/III/2020/1/20200101",
                    "role_candidate": "published_instrument_or_protocol",
                    "content_type": "text/html",
                    "sha256": "landing",
                    "artifact_path": str(landing),
                },
                {
                    "source_order": 2,
                    "final_url": "https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/deutsch.pdf",
                    "discovered_from_url": "https://www.ris.bka.gv.at/eli/bgbl/III/2020/1/20200101",
                    "role_candidate": "official_text_attachment",
                    "content_type": "application/pdf",
                    "sha256": "de-source",
                    "artifact_path": str(german),
                },
                {
                    "source_order": 3,
                    "final_url": "https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/english.pdf",
                    "discovered_from_url": "https://www.ris.bka.gv.at/eli/bgbl/III/2020/1/20200101",
                    "role_candidate": "official_text_attachment",
                    "content_type": "application/pdf",
                    "sha256": "en-source",
                    "artifact_path": str(english),
                },
            ]
            article_sources = [
                {
                    "source_sha256": "de-source",
                    "article_candidates": [
                        {
                            "article_number": 12,
                            "text_sha256": "de-article",
                            "artifact_path": "artifacts/at/article-de.txt",
                            "substantive_article_candidate": True,
                            "semantic_income_candidate": None,
                        }
                    ],
                },
                {
                    "source_sha256": "en-source",
                    "article_candidates": [
                        {
                            "article_number": 12,
                            "text_sha256": "en-article",
                            "artifact_path": "artifacts/at/article-en.txt",
                            "substantive_article_candidate": True,
                            "semantic_income_candidate": None,
                        }
                    ],
                },
            ]
        elif index == 1:
            sources = [
                {
                    "source_order": 1,
                    "final_url": "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Artikel=12&Gesetzesnummer=1",
                    "role_candidate": "current_consolidated_view",
                    "content_type": "text/html",
                    "sha256": "current",
                    "artifact_path": str(current),
                }
            ]
            article_sources = [
                {
                    "source_sha256": "current",
                    "article_candidates": [
                        {
                            "article_number": 12,
                            "text_sha256": "current-article",
                            "artifact_path": "artifacts/at/current-article.txt",
                            "substantive_article_candidate": True,
                            "semantic_income_candidate": None,
                        }
                    ],
                }
            ]
        else:
            sources = [
                {
                    "source_order": 1,
                    "final_url": f"https://www.ris.bka.gv.at/eli/bgbl/III/2020/{index}/20200101",
                    "role_candidate": "published_instrument_or_protocol",
                    "content_type": "application/pdf",
                    "sha256": f"source-{index}",
                    "artifact_path": str(german),
                }
            ]
            article_sources = []

        partners.append({"partner_label": label, "sources": sources})
        article_partners.append({"partner_label": label, "sources": article_sources})

    pilot = {
        "source_country": "AT",
        "pilot_partner_count": 89,
        "partners": partners,
    }
    articles = {
        "source_country": "AT",
        "partner_count": 89,
        "partners": article_partners,
    }
    return pilot, articles


def test_at_language_evidence_tracks_german_and_english_without_releasing_wording(tmp_path: Path):
    pilot, articles = _fixture(tmp_path)
    evidence = build_language_evidence(pilot, articles, artifact_root=tmp_path)
    row = evidence["partners"][0]

    assert evidence["schema_version"] == 1
    assert evidence["partner_count"] == 89
    assert row["language_evidence_coverage_machine"] == {
        "german_official_source_candidate_available": True,
        "english_official_source_candidate_available": True,
        "unknown_language_source_count": 1,
    }
    article_languages = {item["text_sha256"]: item["language_candidate"] for item in row["article_language_evidence"]}
    assert article_languages == {"de-article": "de", "en-article": "en"}
    assert all(item["text_authority_candidate"] == "not_adjudicated" for item in row["article_language_evidence"])
    assert row["step4_web_wording_readiness"]["de"] is False
    assert row["step4_web_wording_readiness"]["en"] is False
    assert row["translated_en_from_controlling_text"]["status"] == "not_created"
    assert row["web_wording_released"] is False


def test_at_current_consolidated_view_is_german_language_candidate_not_authenticity_conclusion(tmp_path: Path):
    pilot, articles = _fixture(tmp_path)
    row = build_language_evidence(pilot, articles, artifact_root=tmp_path)["partners"][1]
    source = row["source_language_evidence"][0]
    article = row["article_language_evidence"][0]

    assert source["language_candidate"] == "de"
    assert source["language_evidence_method"] == "official_austrian_consolidated_view"
    assert source["text_authority_candidate"] == "not_adjudicated"
    assert article["language_candidate"] == "de"
    assert row["step4_web_wording_readiness"]["de"] is False


def test_at_unknown_language_source_never_becomes_english_by_assumption(tmp_path: Path):
    pilot, articles = _fixture(tmp_path)
    row = build_language_evidence(pilot, articles, artifact_root=tmp_path)["partners"][2]
    assert row["source_language_evidence"][0]["language_candidate"] == "unknown"
    assert row["language_evidence_coverage_machine"]["english_official_source_candidate_available"] is False
    assert row["translated_en_from_controlling_text"]["translation_text"] is None
    assert row["web_wording_released"] is False


def test_at_language_evidence_rejects_partial_partner_population(tmp_path: Path):
    pilot, articles = _fixture(tmp_path)
    pilot["pilot_partner_count"] = 88
    try:
        build_language_evidence(pilot, articles, artifact_root=tmp_path)
    except ValueError as exc:
        assert "full 89-partner" in str(exc)
    else:
        raise AssertionError("Expected fail-closed rejection of partial AT language evidence population")
