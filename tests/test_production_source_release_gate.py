import json
from pathlib import Path

ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)


def load(name):
    return json.loads(
        (ROOT / name).read_text(
            encoding="utf-8"
        )
    )


def test_release_gate_covers_all_partners():
    payload = load(
        "production_source_release_gate.json"
    )

    assert payload[
        "treaty_partner_count"
    ] == 98

    assert len(
        payload["treaty_partners"]
    ) == 98

    assert len({
        row["treaty_pair_id"]
        for row in payload[
            "treaty_partners"
        ]
    }) == 98


def test_workstreams_cover_clean_and_remaining():
    payload = load(
        "production_source_release_gate.json"
    )

    clean = [
        row
        for row in payload["treaty_partners"]
        if row["workstream"]
        == "clean_candidate_verification"
    ]

    remediation = [
        row
        for row in payload["treaty_partners"]
        if row["workstream"]
        == "source_remediation"
    ]

    assert len(clean) == 23
    assert len(remediation) == 75


def test_all_gate_fields_are_required():
    payload = load(
        "production_source_release_gate.json"
    )

    expected = {
        "official_source_identity_verified",
        "official_document_hash_verified",
        "clean_text_verified",
        "article_10_verified",
        "article_11_verified",
        "article_12_verified",
        "protocol_inventory_complete",
        "protocol_overlay_verified",
        "mli_status_verified",
        "mli_overlay_verified",
        "authentic_languages_verified",
        "prevailing_language_rule_verified",
        "official_english_version_assessed",
        "withholding_effective_date_verified",
        "legal_rule_mapping_verified",
        "end_to_end_tests_passed",
    }

    for row in payload["treaty_partners"]:
        assert set(row["release_gate"]) == expected
        assert set(row["release_blockers"]) == expected


def test_no_unverified_entry_can_be_active():
    payload = load(
        "production_source_release_gate.json"
    )

    assert payload["active_rule_count"] == 0
    assert payload["production_ready_count"] == 0

    for row in payload["treaty_partners"]:
        assert row["release_status"] == "blocked"
        assert row["active_rule_allowed"] is False
        assert row["legal_text_verified"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True


def test_gate_semantics_are_fail_closed():
    payload = load(
        "production_source_release_gate.json"
    )

    semantics = payload["gate_semantics"]

    assert semantics[
        "all_gate_fields_required"
    ] is True

    assert semantics[
        "partial_completion_allows_active_rule"
    ] is False

    assert semantics[
        "missing_evidence_allows_active_rule"
    ] is False

    assert semantics[
        "automated_extraction_is_legal_verification"
    ] is False

    assert semantics[
        "hash_match_is_legal_verification"
    ] is False

    assert semantics[
        "blocked_entry_result"
    ] == "fail_closed"


def test_summary_matches_gate():
    payload = load(
        "production_source_release_gate.json"
    )

    summary = load(
        "production_source_release_gate_summary.json"
    )

    assert summary[
        "treaty_partner_count"
    ] == 98

    assert sum(
        summary[
            "release_status_counts"
        ].values()
    ) == 98
