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
        (ROOT / name).read_text(encoding="utf-8")
    )


def test_manifest_covers_all_partners_and_scopes():
    payload = load("treaty_source_manifest.json")

    assert payload["treaty_partner_count"] == 98
    assert len(payload["treaty_partners"]) == 98

    packet_ids = [
        packet_id
        for partner in payload["treaty_partners"]
        for packet_id in partner["covered_packet_ids"]
    ]

    assert len(packet_ids) == 294
    assert len(set(packet_ids)) == 294


def test_every_partner_covers_three_income_types():
    payload = load("treaty_source_manifest.json")

    for partner in payload["treaty_partners"]:
        assert partner["covered_income_types"] == [
            "dividend",
            "interest",
            "royalty",
        ]
        assert len(partner["covered_packet_ids"]) == 3


def test_every_manifest_entry_is_fail_closed():
    payload = load("treaty_source_manifest.json")

    for partner in payload["treaty_partners"]:
        assert partner["fail_closed"] is True
        assert (
            partner["promotable_to_active_rules"]
            is False
        )
        assert partner["manifest_status"] in {
            "production_source_ready",
            "source_remediation_required",
        }


def test_damaged_ocr_is_a_blocker():
    payload = load("treaty_source_manifest.json")

    for partner in payload["treaty_partners"]:
        if partner["text_quality"][
            "damaged_ocr_detected"
        ]:
            assert (
                "damaged_ocr_requires_replacement"
                in partner["production_blockers"]
            )
            assert (
                partner["manifest_status"]
                == "source_remediation_required"
            )


def test_production_semantics_are_strict():
    payload = load("treaty_source_manifest.json")
    semantics = payload[
        "production_readiness_semantics"
    ]

    assert semantics["official_source_identity_required"] is True
    assert semantics["document_hash_required"] is True
    assert semantics["language_authority_required"] is True
    assert semantics["clean_text_required"] is True
    assert semantics[
        "article_10_12_mapping_required"
    ] is True
    assert semantics[
        "effective_date_verification_required"
    ] is True
    assert semantics["damaged_ocr_permitted"] is False
    assert (
        semantics["missing_requirement_result"]
        == "fail_closed"
    )


def test_summary_matches_manifest():
    payload = load("treaty_source_manifest.json")
    summary = load(
        "treaty_source_manifest_summary.json"
    )

    assert summary["treaty_partner_count"] == 98
    assert summary["scope_count"] == 294
    assert sum(
        summary["manifest_status_counts"].values()
    ) == 98

    assert len({
        partner["treaty_pair_id"]
        for partner in payload["treaty_partners"]
    }) == 98
