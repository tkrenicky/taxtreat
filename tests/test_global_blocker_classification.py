from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from taxtreat.tools.build_global_blocker_classification import (
    build_classification,
    build_summary,
    classify_pack,
    main,
)


ROOT = Path(__file__).parents[1]

CLASSIFICATION_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "global_blocker_classification.json"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "global_blocker_summary.json"
)


def _classification():
    return json.loads(
        CLASSIFICATION_PATH.read_text(
            encoding="utf-8"
        )
    )


def _summary():
    return json.loads(
        SUMMARY_PATH.read_text(
            encoding="utf-8"
        )
    )


def _scope(
    country: str,
    income_type: str,
):
    return next(
        row
        for row in _classification()["scopes"]
        if row["recipient_country"] == country
        and row["income_type"] == income_type
    )


def test_classification_covers_all_scopes():
    payload = _classification()

    assert payload["scope_count"] == 300
    assert payload["country_count"] == 100
    assert len(payload["scopes"]) == 300

    assert len({
        (
            row["source_country"],
            row["recipient_country"],
            row["income_type"],
        )
        for row in payload["scopes"]
    }) == 300


def test_classification_remains_fail_closed():
    for row in _classification()["scopes"]:
        assert row["status"] == (
            "awaiting_primary_review"
        )
        assert row["candidate_readiness"] == (
            "blocked"
        )
        assert row["approval_eligible"] is False
        assert (
            row["promotable_to_active_rules"]
            is False
        )
        assert row["classification_status"] == (
            "classified_fail_closed"
        )


def test_at_ch_are_pilot_structure_exceptions():
    expected = {
        (
            country,
            income_type,
        )
        for country in ("AT", "CH")
        for income_type in (
            "dividend",
            "interest",
            "royalty",
        )
    }

    actual = {
        (
            row["recipient_country"],
            row["income_type"],
        )
        for row in _classification()["scopes"]
        if row["pilot_structure_exception"]
    }

    assert actual == expected

    for country, income_type in expected:
        row = _scope(
            country,
            income_type,
        )
        assert row[
            "primary_blocker_category"
        ] == "instrument_chain_blocker"


def test_belarus_and_russia_require_status_review():
    for country in ("BY", "RU"):
        for income_type in (
            "dividend",
            "interest",
            "royalty",
        ):
            row = _scope(
                country,
                income_type,
            )

            assert (
                "hard_legal_status_blocker"
                in row["blocker_categories"]
            )
            assert (
                row[
                    "primary_blocker_category"
                ]
                == "hard_legal_status_blocker"
            )
            assert (
                row[
                    "requires_special_status_review"
                ]
                is True
            )


def test_us_interest_has_no_artificial_hard_blocker():
    row = _scope("US", "interest")

    assert (
        row["primary_blocker_category"]
        == "domestic_or_eu_relief_review"
    )
    assert (
        row["requires_special_status_review"]
        is False
    )
    assert row[
        "instrument_chain_present"
    ] is True


def test_german_dividend_has_relief_and_mli_tracks():
    row = _scope("DE", "dividend")

    assert (
        "domestic_or_eu_relief_review"
        in row["blocker_categories"]
    )
    assert row[
        "requires_domestic_or_relief_review"
    ] is True


def test_classification_hashes_are_stable():
    for row in _classification()["scopes"]:
        expected = row.pop(
            "classification_sha256"
        )

        actual = hashlib.sha256(
            json.dumps(
                row,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        assert actual == expected


def test_summary_matches_classification():
    classification = _classification()
    summary = _summary()

    assert summary == build_summary(
        classification
    )
    assert summary["scope_count"] == 300
    assert summary["country_count"] == 100
    assert summary[
        "approval_eligible_scopes"
    ] == 0
    assert summary["promotable_scopes"] == 0
    assert summary["fail_closed"] is True


def test_generation_is_deterministic():
    assert build_classification() == (
        _classification()
    )


def test_classifier_rejects_unknown_blocker():
    pack = {
        "packet_id": "CZ-XX-INT-LEGAL-REVIEW",
        "source_country": "CZ",
        "recipient_country": "XX",
        "recipient_country_name": "Example",
        "income_type": "interest",
        "status": "awaiting_primary_review",
        "candidate_readiness": "blocked",
        "approval_eligible": False,
        "promotable_to_active_rules": False,
        "blockers": ["unknown_blocker"],
        "legal_layers": {
            "instrument_chain": {},
        },
        "review_pack_sha256": "a" * 64,
    }

    with pytest.raises(
        ValueError,
        match="recognised blocker",
    ):
        classify_pack(
            pack,
            pack_file="example.json",
        )


def test_main_writes_outputs(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_blocker_classification as module

    classification_path = (
        tmp_path / "classification.json"
    )
    summary_path = (
        tmp_path / "summary.json"
    )

    monkeypatch.setattr(
        module,
        "OUTPUT_CLASSIFICATION",
        classification_path,
    )
    monkeypatch.setattr(
        module,
        "OUTPUT_SUMMARY",
        summary_path,
    )
    monkeypatch.setattr(
        module,
        "OUTPUT_DIR",
        tmp_path,
    )

    main()

    assert classification_path.exists()
    assert summary_path.exists()


def _minimal_pack(
    blockers,
    *,
    status="awaiting_primary_review",
    approval_eligible=False,
    promotable=False,
):
    return {
        "packet_id": "CZ-XX-INT-LEGAL-REVIEW",
        "source_country": "CZ",
        "recipient_country": "XX",
        "recipient_country_name": "Example",
        "income_type": "interest",
        "status": status,
        "candidate_readiness": "blocked",
        "approval_eligible": approval_eligible,
        "promotable_to_active_rules": promotable,
        "blockers": blockers,
        "legal_layers": {
            "instrument_chain": {},
        },
        "review_pack_sha256": "a" * 64,
    }


@pytest.mark.parametrize(
    "blocker, expected_category, expected_track",
    [
        (
            "protocol_effect_candidate_review",
            "protocol_or_effective_date_blocker",
            "protocol_and_effective_date_review",
        ),
        (
            "mli_effect_candidate_review",
            "mli_ppt_review",
            "mli_review",
        ),
        (
            "semantic_rate_review",
            "treaty_semantic_review",
            "treaty_semantic_review",
        ),
        (
            "independent_legal_review",
            "human_confirmation_only",
            "primary_legal_confirmation",
        ),
    ],
)
def test_additional_primary_categories(
    blocker,
    expected_category,
    expected_track,
):
    row = classify_pack(
        _minimal_pack([blocker]),
        pack_file="example.json",
    )

    assert (
        row["primary_blocker_category"]
        == expected_category
    )
    assert row["review_track"] == expected_track


def test_classifier_rejects_non_list_blockers():
    pack = _minimal_pack([])
    pack["blockers"] = "independent_legal_review"

    with pytest.raises(
        ValueError,
        match="blockers must be a list",
    ):
        classify_pack(
            pack,
            pack_file="example.json",
        )


def test_build_rejects_wrong_pack_count(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_blocker_classification as module

    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="Expected 300 review packs",
    ):
        module.build_classification()


def test_build_rejects_duplicate_scopes(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_blocker_classification as module

    pack = _minimal_pack(
        ["independent_legal_review"]
    )

    for index in range(300):
        path = tmp_path / f"pack-{index:03d}.json"
        path.write_text(
            json.dumps(pack),
            encoding="utf-8",
        )

    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="duplicate scopes",
    ):
        module.build_classification()


def test_build_rejects_non_fail_closed_scope(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_blocker_classification as module

    for index in range(300):
        country = f"{index:03d}"

        pack = {
            **_minimal_pack(
                ["independent_legal_review"]
            ),
            "packet_id": (
                f"CZ-{country}-INT-LEGAL-REVIEW"
            ),
            "recipient_country": country,
        }

        if index == 0:
            pack["approval_eligible"] = True

        path = tmp_path / f"pack-{index:03d}.json"
        path.write_text(
            json.dumps(pack),
            encoding="utf-8",
        )

    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="must remain fail-closed",
    ):
        module.build_classification()
