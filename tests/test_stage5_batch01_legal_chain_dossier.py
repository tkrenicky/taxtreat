import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DOSSIER = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_legal_chain_dossier.json"
)

EXPECTED_COUNTRIES = {
    "AE",
    "BE",
    "BY",
    "EE",
    "GR",
    "HR",
    "KZ",
    "MD",
    "NG",
    "NL",
}


def load(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def scopes(data):
    return [
        scope
        for entry in data["entries"]
        for scope in entry["scopes"]
    ]


def test_batch01_legal_chain_has_exact_coverage():
    data = load(DOSSIER)

    assert (
        set(data["batch"]["countries"])
        == EXPECTED_COUNTRIES
    )

    assert data["batch"]["country_count"] == 10
    assert data["batch"]["scope_count"] == 30

    rows = scopes(data)

    assert len(rows) == 30

    assert len(
        {
            row["scope_id"]
            for row in rows
        }
    ) == 30


def test_each_country_has_articles_10_11_12_evidence_slots():
    data = load(DOSSIER)

    for entry in data["entries"]:

        assert (
            set(entry["article_evidence"])
            == {"10", "11", "12"}
        )

        for article in ("10", "11", "12"):

            item = entry[
                "article_evidence"
            ][article]

            assert (
                item["article_number"]
                == int(article)
            )

            assert isinstance(
                item["resolved"],
                bool,
            )

            assert isinstance(
                item["evidence_count"],
                int,
            )

            assert isinstance(
                item["evidence"],
                list,
            )


def test_income_scope_maps_to_correct_treaty_article():
    data = load(DOSSIER)

    expected = {
        "dividend": 10,
        "interest": 11,
        "royalty": 12,
    }

    for row in scopes(data):

        assert (
            row["treaty_article"]
            == expected[
                row["income_type"]
            ]
        )


def test_all_scopes_remain_fail_closed():
    data = load(DOSSIER)

    assert (
        data[
            "production_releasable_scope_count"
        ]
        == 0
    )

    assert (
        data["terminal_status_counts"]
        == {
            "verified": 0,
            "blocked": 0,
            "pending": 30,
        }
    )

    for row in scopes(data):

        assert (
            row["verification_status"]
            == "needs_review"
        )

        assert (
            row["stage5_terminal_status"]
            == "pending"
        )

        assert (
            row["production_releasable"]
            is False
        )

        assert (
            row[
                "human_primary_review_complete"
            ]
            is False
        )

        assert (
            row[
                "independent_approval_complete"
            ]
            is False
        )


def test_country_entries_remain_fail_closed():
    data = load(DOSSIER)

    for entry in data["entries"]:

        assert (
            entry["verification_status"]
            == "needs_review"
        )

        assert (
            entry["stage5_terminal_status"]
            == "pending"
        )

        assert (
            entry["production_releasable"]
            is False
        )


def test_source_dataset_hashes_match_repository():
    data = load(DOSSIER)

    for relative, expected in (
        data["source_hashes"].items()
    ):

        path = ROOT / relative

        assert path.is_file()

        assert sha256(path) == expected


def test_canonical_parsed_sources_are_hash_bound():
    data = load(DOSSIER)

    for entry in data["entries"]:

        source = entry[
            "canonical_treaty_source"
        ]

        parsed = ROOT / source[
            "parsed_path"
        ]

        artifact = ROOT / source[
            "artifact_uri"
        ]

        assert parsed.is_file()
        assert artifact.is_file()

        assert (
            sha256(parsed)
            == source["parsed_sha256"]
        )

        assert (
            sha256(artifact)
            == source["artifact_sha256"]
        )


def test_remaining294_is_explicitly_reference_only():
    data = load(DOSSIER)

    assert (
        data["safety_boundary"][
            "legacy_remaining294_is_reference_only"
        ]
        is True
    )

    for entry in data["entries"]:

        assert (
            entry[
                "legacy_remaining294_reference"
            ]["reference_only"]
            is True
        )


def test_dossier_does_not_generate_rate_or_legal_conclusion():
    data = load(DOSSIER)

    forbidden = {
        "applicable_rate",
        "recommended_rate",
        "recommended_treatment",
        "final_rate",
        "legal_conclusion",
        "production_rule",
        "verified_rule",
        "applicable_treatment",
    }

    def walk(value):

        if isinstance(value, dict):

            for key, item in value.items():

                assert key not in forbidden
                walk(item)

        elif isinstance(value, list):

            for item in value:
                walk(item)

    walk(data)


def test_no_reviewer_or_approver_is_fabricated():
    data = load(DOSSIER)

    forbidden = {
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

    walk(data)


def test_mli_specific_evidence_is_preserved_for_ee_and_ng():
    data = load(DOSSIER)

    index = {
        entry["country"]: entry
        for entry in data["entries"]
    }

    assert (
        index["EE"]["mli_layer"][
            "batch01_specific_evidence"
        ]
        is not None
    )

    assert (
        index["NG"]["mli_layer"][
            "batch01_specific_evidence"
        ]
        is not None
    )


def test_status_instruments_are_not_silently_interpreted():
    data = load(DOSSIER)

    for entry in data["entries"]:

        status = entry[
            "related_instrument_chain"
        ]["status_instruments"]

        if status:

            assert (
                "status_instrument_effect_requires_human_review"
                in entry[
                    "country_level_gaps"
                ]
            )
