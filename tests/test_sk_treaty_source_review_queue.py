from __future__ import annotations

from taxtreat.tools.build_sk_treaty_source_review_queue import (
    build_queue,
    build_summary,
)


def test_sk_treaty_source_queue_covers_all_relationships_and_scopes():
    payload = build_queue()
    summary = build_summary(payload)

    assert payload["source_country"] == "SK"
    assert payload["relationship_count"] == 75
    assert payload["scope_count"] == 225
    assert len(payload["relationships"]) == 75
    assert len(payload["scopes"]) == 225
    assert len({row["recipient_country"] for row in payload["relationships"]}) == 75
    assert len({row["packet_id"] for row in payload["scopes"]}) == 225

    assert summary["semantic_extraction_completed_scopes"] == 0
    assert summary["review_ready_scopes"] == 0
    assert summary["human_reviewed_scopes"] == 0
    assert summary["production_released_scopes"] == 0


def test_standard_slov_lex_publications_get_deterministic_primary_urls():
    payload = build_queue()
    by_country = {
        row["recipient_country"]: row
        for row in payload["relationships"]
    }

    assert by_country["AT"]["treaty_publication"] == "48/1979"
    assert by_country["AT"]["official_primary_text_url"].endswith("/1979/48/")
    assert by_country["AT"]["primary_text_source_status"] == "official_slov_lex_url_ready"

    assert by_country["NZ"]["treaty_publication"] == "243/2024"
    assert by_country["NZ"]["official_primary_text_url"].endswith("/2024/243/")


def test_non_standard_primary_sources_are_flagged_not_guessed():
    payload = build_queue()
    non_standard = [
        row
        for row in payload["relationships"]
        if row["primary_text_source_status"]
        == "non_standard_primary_source_resolution_required"
    ]

    assert all(row["official_primary_text_url"] is None for row in non_standard)
    for row in non_standard:
        scopes = [
            scope
            for scope in payload["scopes"]
            if scope["recipient_country"] == row["recipient_country"]
        ]
        assert len(scopes) == 3
        assert all(
            "non_standard_primary_source_resolution_pending"
            in scope["release_blockers"]
            for scope in scopes
        )


def test_instrument_chain_blockers_are_preserved():
    payload = build_queue()
    by_packet = {row["packet_id"]: row for row in payload["scopes"]}

    assert "protocol_overlay_pending" in by_packet[
        "SK-NL-royalty-TREATY-SOURCE"
    ]["release_blockers"]
    assert "correction_notice_pending" in by_packet[
        "SK-FR-dividend-TREATY-SOURCE"
    ]["release_blockers"]
    assert "pair_specific_mli_overlay_pending" in by_packet[
        "SK-AT-interest-TREATY-SOURCE"
    ]["release_blockers"]
    assert "pair_specific_mli_overlay_pending" not in by_packet[
        "SK-US-dividend-TREATY-SOURCE"
    ]["release_blockers"]


def test_treaty_source_queue_remains_fail_closed():
    payload = build_queue()

    assert payload["policy"]["official_primary_source_required"] is True
    assert payload["policy"]["non_standard_sources_must_not_be_guessed"] is True
    assert payload["policy"][
        "human_review_starts_only_after_all_machine_evidence_is_ready"
    ] is True

    assert all(not row["review_ready"] for row in payload["scopes"])
    assert all(not row["approval_eligible"] for row in payload["scopes"])
    assert all(
        row["runtime_status"] == "not_released"
        for row in payload["scopes"]
    )
