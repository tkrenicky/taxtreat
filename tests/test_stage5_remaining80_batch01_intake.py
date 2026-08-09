import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MANIFEST = (
    ROOT
    / "data/legal_consolidation/"
    "stage5_execution_manifest.json"
)

INTAKE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_intake.json"
)

SOURCE_MANIFEST = (
    ROOT
    / "data/manifests/"
    "source_manifest.json"
)


def load(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def digest(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def all_scopes(data):
    return [
        scope
        for entry in data["entries"]
        for scope in entry["scopes"]
    ]


def test_batch01_matches_execution_manifest():
    manifest = load(MANIFEST)
    intake = load(INTAKE)

    expected = (
        manifest[
            "remaining80_work_batches"
        ][0]["countries"]
    )

    assert intake["batch"]["countries"] == expected
    assert intake["batch"]["country_count"] == 10
    assert intake["batch"]["scope_count"] == 30


def test_batch01_has_30_unique_scopes():
    intake = load(INTAKE)
    scopes = all_scopes(intake)

    assert len(intake["entries"]) == 10
    assert len(scopes) == 30

    assert len(
        {
            row["scope_id"]
            for row in scopes
        }
    ) == 30


def test_all_10_canonical_parsed_sources_resolve():
    intake = load(INTAKE)

    assert (
        intake[
            "canonical_base_treaty_source_resolution"
        ]
        == {
            "resolved": 10,
            "unresolved": 0,
        }
    )

    for entry in intake["entries"]:

        source = entry[
            "canonical_base_treaty_source"
        ]

        assert (
            source["resolution_status"]
            == "resolved_via_source_manifest"
        )

        parsed = ROOT / source["parsed_path"]

        assert parsed.is_file()

        assert (
            digest(parsed)
            == source["parsed_sha256"]
        )


def test_all_10_sources_have_manifest_identity():
    intake = load(INTAKE)

    for entry in intake["entries"]:

        source = entry[
            "canonical_base_treaty_source"
        ]

        assert source["source_id"]
        assert source["source_title"]

        assert source["artifact_uri"]
        assert source["artifact_sha256"]

        artifact = (
            ROOT / source["artifact_uri"]
        )

        assert artifact.is_file()

        assert (
            digest(artifact)
            == source["artifact_sha256"]
        )


def test_source_manifest_itself_is_hash_bound():
    intake = load(INTAKE)

    expected = intake[
        "source_dataset_hashes"
    ][
        "data/manifests/source_manifest.json"
    ]

    assert digest(SOURCE_MANIFEST) == expected


def test_batch01_remains_fully_fail_closed():
    intake = load(INTAKE)
    scopes = all_scopes(intake)

    assert (
        intake[
            "production_releasable_scope_count"
        ]
        == 0
    )

    assert (
        intake["terminal_status_counts"]
        == {
            "verified": 0,
            "blocked": 0,
            "pending": 30,
        }
    )

    for scope in scopes:

        assert (
            scope["verification_status"]
            == "needs_review"
        )

        assert (
            scope["stage5_terminal_status"]
            == "pending"
        )

        assert (
            scope["production_releasable"]
            is False
        )

        assert (
            scope[
                "human_primary_review_complete"
            ]
            is False
        )

        assert (
            scope[
                "independent_approval_complete"
            ]
            is False
        )


def test_batch01_does_not_create_legal_conclusion():
    intake = load(INTAKE)

    forbidden = {
        "applicable_rate",
        "recommended_rate",
        "recommended_treatment",
        "legal_conclusion",
        "production_rule",
        "final_rate",
        "reviewer",
        "reviewer_id",
        "reviewed_by",
        "approver",
        "approver_id",
        "approved_by",
    }

    def walk(value):

        if isinstance(value, dict):

            for key, item in value.items():

                assert key not in forbidden

                walk(item)

        elif isinstance(value, list):

            for item in value:
                walk(item)

    walk(intake)


def test_legacy_remaining294_is_reference_only():
    intake = load(INTAKE)

    assert (
        intake["safety_boundary"][
            "legacy_remaining_294_is_frozen_reference_only"
        ]
        is True
    )

    for scope in all_scopes(intake):

        assert (
            scope[
                "legacy_remaining_294_reference_present"
            ]
            in {True, False}
        )


def test_candidate_production_boundary_is_explicit():
    intake = load(INTAKE)

    boundary = intake[
        "safety_boundary"
    ]

    assert (
        boundary[
            "official_source_is_authority"
        ]
        is True
    )

    assert (
        boundary[
            "extraction_is_not_verification"
        ]
        is True
    )

    assert (
        boundary[
            "provenance_is_not_approval"
        ]
        is True
    )

    assert (
        boundary[
            "candidate_is_not_production_rule"
        ]
        is True
    )

    assert (
        boundary[
            "human_review_required"
        ]
        is True
    )

    assert (
        boundary[
            "independent_approval_required_before_release"
        ]
        is True
    )

    assert (
        boundary[
            "production_release_created_by_this_dataset"
        ]
        is False
    )
