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


def test_audit_covers_all_resolved_scopes():
    payload = load(
        "global_source_quality_audit.json"
    )

    assert payload["scope_count"] == 294
    assert len(payload["scopes"]) == 294
    assert len({
        row["packet_id"]
        for row in payload["scopes"]
    }) == 294


def test_every_scope_has_source_status():
    payload = load(
        "global_source_quality_audit.json"
    )

    allowed = {
        "production_source_ready",
        "metadata_completion_required",
        "source_remediation_required",
    }

    for row in payload["scopes"]:
        assert row["audit_status"] in allowed
        assert isinstance(row["issues"], list)
        assert row["fail_closed"] is True
        assert (
            row["promotable_to_active_rules"]
            is False
        )


def test_damaged_ocr_cannot_be_ready():
    payload = load(
        "global_source_quality_audit.json"
    )

    for row in payload["scopes"]:
        if row["damaged_ocr_detected"]:
            assert (
                row["audit_status"]
                == "source_remediation_required"
            )
            assert (
                "damaged_ocr_detected"
                in row["issues"]
            )


def test_missing_source_is_fail_closed():
    payload = load(
        "global_source_quality_audit.json"
    )

    for row in payload["scopes"]:
        if not row[
            "official_source_reference_present"
        ]:
            assert (
                "missing_official_source_reference"
                in row["issues"]
            )
            assert row["fail_closed"] is True


def test_summary_matches_audit():
    payload = load(
        "global_source_quality_audit.json"
    )
    summary = load(
        "global_source_quality_audit_summary.json"
    )

    assert summary["scope_count"] == 294
    assert sum(
        summary["status_counts"].values()
    ) == 294

    assert summary["country_count"] == len({
        row["recipient_country"]
        for row in payload["scopes"]
    })


def test_no_audit_result_is_promotable():
    payload = load(
        "global_source_quality_audit.json"
    )

    assert payload["fail_closed"] is True
    assert (
        payload["promotable_to_active_rules"]
        is False
    )
