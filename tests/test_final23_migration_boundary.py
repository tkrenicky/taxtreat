import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BOUNDARY = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "final23_migration_boundary.json"
)

CANDIDATES = (
    ROOT
    / "data"
    / "legal_rule_candidates"
    / "final23"
)


def _boundary():
    return json.loads(
        BOUNDARY.read_text(encoding="utf-8")
    )


def test_final23_migration_boundary_is_explicit():
    data = _boundary()

    countries = data[
        "migrated_recipient_countries"
    ]

    assert len(countries) == 18
    assert len(set(countries)) == 18

    assert (
        data["migrated_scope_count"]
        == 54
    )


def test_legacy_review_hashes_are_frozen():
    data = _boundary()

    assert (
        data["legacy_snapshot"]["status"]
        == "frozen"
    )

    assert (
        data["integrity_rules"][
            "legacy_review_hashes_must_not_be_rewritten"
        ]
        is True
    )


def test_final23_candidates_remain_needs_review():
    files = sorted(
        CANDIDATES.glob("final23_*.json")
    )

    assert len(files) == 18

    rule_count = 0

    for path in files:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )

        for rule in payload["rules"]:
            assert (
                rule["verification_status"]
                == "needs_review"
            )

            rule_count += 1

    assert rule_count == 78


def test_final23_is_not_production_autoloaded():
    data = _boundary()

    assert (
        data["current_candidate_catalog"][
            "production_autoload"
        ]
        is False
    )

    production = (
        ROOT / "data" / "legal_rules"
    )

    assert not list(
        production.glob("final23_*.json")
    )
