import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATA = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_mli_evidence.json"
)

MLI_EFFECTS = (
    ROOT
    / "data/legal_consolidation/"
    "mli_wht_effects.json"
)


def load(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def digest(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def test_mli_evidence_is_fail_closed():
    data = load(DATA)

    assert (
        data["verification_status"]
        == "needs_review"
    )

    assert (
        data["production_releasable"]
        is False
    )

    assert (
        data["result"][
            "production_rules_created"
        ]
        == 0
    )

    assert (
        data["result"][
            "verified_rules_created"
        ]
        == 0
    )


def test_all_source_snapshots_are_hash_bound():
    data = load(DATA)

    for source in (
        data["official_source_snapshots"].values()
    ):

        for path_key, hash_key in (
            ("pdf_path", "pdf_sha256"),
            ("text_path", "text_sha256"),
            ("html_path", "html_sha256"),
        ):

            if path_key not in source:
                continue

            path = ROOT / source[path_key]

            assert path.is_file()

            assert (
                digest(path)
                == source[hash_key]
            )


def test_estonia_is_not_silently_promoted():
    data = load(DATA)

    ee = data["countries"]["EE"]

    assert (
        ee["repository_inventory"][
            "mli_listed"
        ]
        is True
    )

    assert (
        ee["repository_inventory"][
            "mli_notice_available"
        ]
        is True
    )

    assert (
        ee["repository_inventory"][
            "mli_effect_reference_present"
        ]
        is False
    )

    assert (
        ee["candidate_resolution"]["status"]
        == "structured_effect_mapping_pending_review"
    )

    assert (
        ee["candidate_resolution"][
            "verification_status"
        ]
        == "needs_review"
    )

    assert (
        ee["candidate_resolution"][
            "production_releasable"
        ]
        is False
    )


def test_nigeria_remains_review_only():
    data = load(DATA)

    ng = data["countries"]["NG"]

    assert (
        ng["repository_inventory"][
            "mli_listed"
        ]
        is True
    )

    assert (
        ng["repository_inventory"][
            "mli_notice_available"
        ]
        is False
    )

    assert (
        ng["repository_inventory"][
            "mli_effect_reference_present"
        ]
        is False
    )

    assert (
        ng["oecd_current_signatory_evidence"][
            "signature_date_evidenced"
        ]
        == "2017-08-17"
    )

    assert (
        ng["oecd_current_signatory_evidence"][
            "deposit_of_ratification_evidenced"
        ]
        is False
    )

    assert (
        ng["oecd_current_signatory_evidence"][
            "entry_into_force_evidenced"
        ]
        is False
    )

    assert (
        ng["candidate_resolution"]["status"]
        == "counterparty_ratification_not_evidenced"
    )

    assert (
        ng["candidate_resolution"][
            "production_releasable"
        ]
        is False
    )


def test_mli_effects_are_not_modified_by_resolution_dataset():
    raw = MLI_EFFECTS.read_text(
        encoding="utf-8"
    ).upper()

    assert "CZ-EE-MLI-" not in raw
    assert "CZ-NG-MLI-" not in raw


def test_no_human_approval_metadata_is_fabricated():
    data = load(DATA)

    forbidden = {
        "reviewer",
        "reviewed_by",
        "reviewer_id",
        "approver",
        "approved_by",
        "approver_id",
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


def test_original_mechanical_gaps_are_classified():
    data = load(DATA)

    assert (
        data["result"][
            "original_mechanical_gap_count"
        ]
        == 3
    )

    assert (
        data["result"][
            "unclassified_gap_count"
        ]
        == 0
    )
