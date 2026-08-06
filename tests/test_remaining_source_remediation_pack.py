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


def test_pack_covers_remaining_partners():
    payload = load(
        "remaining_source_remediation_pack.json"
    )

    rows = [
        row
        for batch in payload["batches"]
        for row in batch["treaty_partners"]
    ]

    assert payload[
        "treaty_partner_count"
    ] == 75

    assert len(rows) == 75

    assert len({
        row["treaty_pair_id"]
        for row in rows
    }) == 75


def test_expected_batch_sizes():
    payload = load(
        "remaining_source_remediation_pack.json"
    )

    counts = {
        batch["batch_type"]:
            batch["treaty_partner_count"]
        for batch in payload["batches"]
    }

    assert counts == {
        "resolve_source_identity": 1,
        "replace_damaged_text_source": 38,
        "acquire_official_source": 36,
    }


def test_every_entry_has_completion_evidence():
    payload = load(
        "remaining_source_remediation_pack.json"
    )

    for batch in payload["batches"]:
        for row in batch[
            "treaty_partners"
        ]:
            evidence = row[
                "completion_evidence"
            ]

            assert set(evidence) == {
                "official_base_source_url",
                "official_publication_reference",
                "official_document_sha256",
                "clean_text_path",
                "clean_text_sha256",
                "article_10_sha256",
                "article_11_sha256",
                "article_12_sha256",
                "protocol_inventory_complete",
                "mli_overlay_verified",
                "language_authority_verified",
                "withholding_effective_date_verified",
            }

            assert row[
                "remediation_status"
            ] == "not_started"

            assert row[
                "production_ready"
            ] is False

            assert row["fail_closed"] is True


def test_completion_gate_is_strict():
    payload = load(
        "remaining_source_remediation_pack.json"
    )

    gate = payload["completion_gate"]

    assert gate[
        "official_source_identity_required"
    ] is True

    assert gate[
        "official_document_hash_required"
    ] is True

    assert gate[
        "clean_text_required"
    ] is True

    assert gate[
        "articles_10_12_required"
    ] is True

    assert gate[
        "damaged_ocr_permitted"
    ] is False

    assert gate[
        "missing_requirement_result"
    ] == "fail_closed"


def test_summary_matches_pack():
    payload = load(
        "remaining_source_remediation_pack.json"
    )

    summary = load(
        "remaining_source_remediation_pack_summary.json"
    )

    assert summary[
        "treaty_partner_count"
    ] == 75

    assert sum(
        summary["status_counts"].values()
    ) == 75


def test_nothing_is_promoted():
    payload = load(
        "remaining_source_remediation_pack.json"
    )

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload[
        "production_ready"
    ] is False

    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False
