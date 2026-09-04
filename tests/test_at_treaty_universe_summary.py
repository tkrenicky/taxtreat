import json
from pathlib import Path


SUMMARY = Path("data/legal_reviews/at_outbound/treaty_universe_summary_2026.json")


def _summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def test_at_treaty_universe_summary_matches_validated_2026_acquisition():
    data = _summary()

    assert data["source_country"] == "AT"
    assert data["as_of"] == "2026-08-24"
    assert data["status"] == "machine_acquisition_validated_not_released"
    assert data["source_page_record_count"] == 93
    assert data["current_treaty_partner_count"] == 89
    assert data["current_scope_count"] == 267
    assert data["mli_discovery_flag_count"] == 51
    assert data["status_instrument_flag_count"] == 2
    assert len(data["current_partners"]) == 89
    assert len(set(data["current_partners"])) == 89


def test_at_treaty_universe_excludes_noncurrent_source_records_fail_closed():
    data = _summary()
    excluded = {row["partner_label"]: row for row in data["excluded_records"]}

    assert excluded["Argentinien/Argentina"]["applicability_status"] == "in_force_future_effective"
    assert excluded["Argentinien/Argentina"]["effective_from"] == "1.1.2027"
    assert excluded["Libyen / Lybia"]["applicability_status"] == "signed_not_in_force"
    assert excluded["Syrien / Syria"]["applicability_status"] == "signed_not_in_force"
    assert excluded["UdSSR / USSR"]["applicability_status"] == "historical_parent_instrument"

    current = set(data["current_partners"])
    assert current.isdisjoint(excluded)


def test_at_treaty_universe_preserves_status_instrument_review_separately_from_rate_review():
    data = _summary()

    assert set(data["status_instrument_flagged_partners"]) == {
        "Russland / Russia",
        "Weißrussland / Belarus",
    }
    constraints = "\n".join(data["release_constraints"])
    assert "Status-instrument flags are discovery signals only" in constraints
    assert "bilateral matching" in constraints
    assert "Machine extraction does not constitute legal review" in constraints


def test_at_treaty_universe_records_reproducible_acquisition_digest():
    data = _summary()
    digest = data["acquisition_artifact_sha256"]

    assert len(digest) == 64
    int(digest, 16)
