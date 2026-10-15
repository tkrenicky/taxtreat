from taxtreat.tools.reconcile_at_article_text_candidates import reconcile_article_candidates


def _candidate(number, role, digest, income=None):
    return {
        "article_number": number,
        "text_sha256": digest,
        "character_count": 100,
        "artifact_path": f"artifacts/{digest}.txt",
        "substantive_article_candidate": True,
        "semantic_income_detected": income,
        "quality_flags": [],
    }


INVENTORY = {
    "source_country": "AT",
    "status": "article_text_candidates_not_reviewed",
    "partners": [
        {
            "partner_label": "Example / Example",
            "sources": [
                {
                    "source_order": 1,
                    "final_url": "https://www.ris.bka.gv.at/base",
                    "role_candidate": "published_instrument_or_protocol",
                    "source_sha256": "a" * 64,
                    "article_candidates": [
                        _candidate(10, "published_instrument_or_protocol", "1" * 64),
                        _candidate(11, "published_instrument_or_protocol", "2" * 64),
                        _candidate(12, "published_instrument_or_protocol", "3" * 64),
                    ],
                },
                {
                    "source_order": 2,
                    "final_url": "https://www.bmf.gv.at/dam/synth.pdf",
                    "role_candidate": "synthesized_mli_text",
                    "source_sha256": "b" * 64,
                    "article_candidates": [
                        _candidate(10, "synthesized_mli_text", "4" * 64),
                        _candidate(11, "synthesized_mli_text", "5" * 64),
                        _candidate(12, "synthesized_mli_text", "6" * 64),
                    ],
                },
                {
                    "source_order": 3,
                    "final_url": "https://www.ris.bka.gv.at/GeltendeFassung.wxe",
                    "role_candidate": "current_consolidated_view",
                    "source_sha256": "c" * 64,
                    "article_candidates": [
                        _candidate(10, "current_consolidated_view", "7" * 64),
                        _candidate(11, "current_consolidated_view", "8" * 64),
                        _candidate(12, "current_consolidated_view", "9" * 64),
                    ],
                },
            ],
        }
    ],
}


def test_reconciliation_queues_variants_without_selecting_controlling_text_or_rate():
    result = reconcile_article_candidates(INVENTORY)
    assert result["schema_version"] == 3
    assert result["status"] == "article_variant_reconciliation_queue_not_reviewed"
    assert result["partner_count"] == 1
    partner = result["partners"][0]
    assert partner["instrument_chain_reconciliation_completed"] is False
    assert partner["release_eligible"] is False
    for article in partner["articles"]:
        assert article["candidate_count"] == 3
        assert article["unique_text_variant_count"] == 3
        assert article["review_strategy"] == "compare_synthesized_mli_to_current_consolidated_and_published_chain"
        assert article["controlling_text_selected"] is False
        assert article["legal_review_completed"] is False
        assert article["rate_interpretation_released"] is False
    assert [scope["income_type"] for scope in partner["income_scopes"]] == ["dividend", "interest", "royalty"]
    assert [scope["actual_article_numbers_machine"] for scope in partner["income_scopes"]] == [[10], [11], [12]]


def test_reconciliation_retains_nonstandard_actual_article_numbers_by_income():
    inventory = {
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partners": [{
            "partner_label": "Legacy / Legacy",
            "sources": [{
                "source_order": 1,
                "final_url": "https://www.ris.bka.gv.at/legacy",
                "role_candidate": "published_instrument_or_protocol",
                "source_sha256": "d" * 64,
                "article_candidates": [
                    _candidate(8, "published_instrument_or_protocol", "a" * 64, "dividend"),
                    _candidate(9, "published_instrument_or_protocol", "b" * 64, "interest"),
                    _candidate(10, "published_instrument_or_protocol", "c" * 64, "royalty"),
                ],
            }],
        }],
    }
    partner = reconcile_article_candidates(inventory)["partners"][0]
    scopes = {row["income_type"]: row for row in partner["income_scopes"]}
    assert scopes["dividend"]["actual_article_numbers_machine"] == [8]
    assert scopes["interest"]["actual_article_numbers_machine"] == [9]
    assert scopes["royalty"]["actual_article_numbers_machine"] == [10]
    assert all(scopes[income]["nonstandard_article_number_machine"] is True for income in scopes)
    assert all(scopes[income]["conditions_mapped"] is False for income in scopes)


def test_reconciliation_does_not_treat_mli_presence_as_release_or_automatic_conflict():
    result = reconcile_article_candidates(INVENTORY)
    constraints = "\n".join(result["release_constraints"])
    assert "MLI presence by itself does not increase legal-risk classification" in constraints
    assert "Different hashes are evidence variants, not automatically legal conflicts" in constraints
    assert "rate-to-condition mapping" in constraints
