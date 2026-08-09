import json
import hashlib
from pathlib import Path

PATH = Path(
    "data/legal_reviews/global_cz_outbound/"
    "final23_semantic_runtime_candidates.json"
)

def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )

def test_all_54_scopes_present():
    data = load()

    assert len(data["records"]) == 54
    assert data["summary"]["scope_count"] == 54

def test_semantic_rates_never_exceed_reconciled_numeric_set():
    data = load()

    for row in data["records"]:
        assert set(
            row["semantic_candidate_rates"]
        ).issubset(
            set(row["numeric_candidate_rates"])
        )

def test_complete_semantic_scope_has_full_rate_coverage():
    data = load()

    for row in data["records"]:
        if not row["semantic_mapping_complete"]:
            continue

        assert row["full_rate_coverage"] is True
        assert (
            row["condition_mapping_complete"]
            is True
        )

        assert set(
            row["semantic_candidate_rates"]
        ) == set(
            row["numeric_candidate_rates"]
        )

def test_runtime_candidates_are_still_fail_closed():
    data = load()

    assert data["production_ready"] is False
    assert data["fail_closed"] is True
    assert (
        data["summary"][
            "runtime_verified_rule_count"
        ]
        == 0
    )

    for row in data["records"]:
        assert row["runtime_candidates_verified"] is False
        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True

        for rule in row["runtime_candidates"]:
            assert (
                rule["verification_status"]
                == "needs_review"
            )

def test_runtime_source_hashes_match_text():
    data = load()

    for row in data["records"]:
        for rule in row["runtime_candidates"]:
            actual = hashlib.sha256(
                rule["source_text"].encode("utf-8")
            ).hexdigest()

            assert (
                actual
                == rule["source_excerpt_hash"]
            )

def test_multi_rate_scopes_require_explicit_conditions():
    data = load()

    for row in data["records"]:
        if len(row["numeric_candidate_rates"]) <= 1:
            continue

        if row["semantic_mapping_complete"]:
            assert all(
                candidate["conditions"]
                for candidate
                in row["semantic_candidates"]
            )
