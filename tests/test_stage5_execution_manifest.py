import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MANIFEST = (
    ROOT / "data/legal_consolidation/stage5_execution_manifest.json"
)

FINAL23_DIR = ROOT / "data/legal_rule_candidates/final23"

MIGRATION_BOUNDARY = (
    ROOT / "data/legal_consolidation/final23_migration_boundary.json"
)

STAGE4_GATE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage4_final_runtime_release_gate.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_stage5_manifest_covers_exactly_100_countries_and_300_scopes():
    data = load(MANIFEST)

    assert data["universe"]["country_count"] == 100
    assert data["universe"]["scope_count"] == 300
    assert len(data["scopes"]) == 300

    scope_ids = {row["scope_id"] for row in data["scopes"]}

    assert len(scope_ids) == 300

    countries = {
        row["recipient_country"]
        for row in data["scopes"]
    }

    assert len(countries) == 100


def test_stage5_cohorts_are_disjoint_and_complete():
    data = load(MANIFEST)

    pilot = set(data["cohorts"]["pilot_at_ch"]["countries"])
    final23 = set(data["cohorts"]["final23"]["countries"])
    remaining80 = set(data["cohorts"]["remaining80"]["countries"])

    assert pilot == {"AT", "CH"}

    assert len(final23) == 18
    assert len(remaining80) == 80

    assert not pilot & final23
    assert not pilot & remaining80
    assert not final23 & remaining80

    assert len(pilot | final23 | remaining80) == 100

    assert data["cohorts"]["pilot_at_ch"]["scope_count"] == 6
    assert data["cohorts"]["final23"]["scope_count"] == 54
    assert data["cohorts"]["remaining80"]["scope_count"] == 240


def test_final23_remains_candidate_only_and_needs_review():
    data = load(MANIFEST)

    final23 = data["cohorts"]["final23"]

    assert final23["candidate_rule_count"] == 78
    assert final23["verification_status"] == "needs_review"

    assert (
        data["migration_boundary"]["final23_verification_status_counts"]
        == {"needs_review": 78}
    )

    assert len(list(FINAL23_DIR.glob("*.json"))) == 18

    production = ROOT / "data/legal_rules"

    assert not list(production.glob("final23_*.json"))


def test_stage4_runtime_completion_is_not_legal_release():
    manifest = load(MANIFEST)
    gate = load(STAGE4_GATE)

    assert gate["stage4_complete"] is True
    assert gate["production_legal_release_complete"] is False

    assert manifest["stage4_boundary"]["stage4_complete"] is True

    assert (
        manifest["stage4_boundary"]["production_legal_release_complete"]
        is False
    )


def test_migration_boundary_is_hash_bound():
    data = load(MANIFEST)

    assert (
        data["migration_boundary"]["sha256"]
        == digest(MIGRATION_BOUNDARY)
    )


def test_frozen_remaining_294_files_are_hash_bound():
    data = load(MANIFEST)

    frozen = data["frozen_remaining_294_hashes"]

    assert frozen

    for relative_path, expected_hash in frozen.items():
        path = ROOT / relative_path

        assert path.is_file()
        assert digest(path) == expected_hash


def test_no_stage5_scope_is_silently_released():
    data = load(MANIFEST)

    for scope in data["scopes"]:
        assert scope["stage5_status"] == "pending"
        assert scope["production_releasable"] is False

        assert (
            scope["required_terminal_status"]
            == "verified_or_blocked"
        )

        assert scope["human_primary_review_required"] is True

        assert (
            scope["independent_approval_required_if_verified"]
            is True
        )


def test_remaining80_is_split_into_eight_repeatable_batches():
    data = load(MANIFEST)

    batches = data["remaining80_work_batches"]

    assert len(batches) == 8

    countries = []

    for batch in batches:
        assert batch["country_count"] == 10
        assert batch["scope_count"] == 30
        countries.extend(batch["countries"])

    assert len(countries) == 80
    assert len(set(countries)) == 80

    assert set(countries) == set(
        data["cohorts"]["remaining80"]["countries"]
    )


def test_manifest_contains_no_fabricated_human_approval():
    data = load(MANIFEST)

    forbidden_keys = {
        "reviewer",
        "reviewer_id",
        "approver",
        "approver_id",
        "approved_by",
        "reviewed_by",
    }

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                assert key not in forbidden_keys
                walk(item)

        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(data)


def test_stage5_milestones_are_monotonic_and_end_at_100():
    data = load(MANIFEST)

    percentages = [
        row["percent"]
        for row in data["stage5_milestones"]
    ]

    assert percentages == [5, 20, 40, 55, 70, 85, 98, 100]
