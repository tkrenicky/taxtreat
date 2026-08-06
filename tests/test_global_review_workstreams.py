from __future__ import annotations

import hashlib
import json
from pathlib import Path

from taxtreat.tools.build_global_review_workstreams import (
    build_summary,
    build_workstreams,
)


ROOT = Path(__file__).parents[1]

GLOBAL_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

WORKSTREAMS_PATH = (
    GLOBAL_DIR
    / "global_review_workstreams.json"
)

SUMMARY_PATH = (
    GLOBAL_DIR
    / "global_review_workstreams_summary.json"
)


def _payload():
    return json.loads(
        WORKSTREAMS_PATH.read_text(
            encoding="utf-8"
        )
    )


def _summary():
    return json.loads(
        SUMMARY_PATH.read_text(
            encoding="utf-8"
        )
    )


def _scope(country, income_type):
    return next(
        row
        for row in _payload()["scopes"]
        if row["recipient_country"] == country
        and row["income_type"] == income_type
    )


def test_all_scopes_are_assigned():
    payload = _payload()

    assert payload["scope_count"] == 300
    assert payload["country_count"] == 100
    assert len(payload["scopes"]) == 300

    assert len({
        row["packet_id"]
        for row in payload["scopes"]
    }) == 300


def test_all_scopes_remain_fail_closed():
    for row in _payload()["scopes"]:
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
        assert row["review_status"] == (
            "workstreams_assigned_fail_closed"
        )


def test_every_scope_has_core_reviews():
    required = {
        "czech_domestic_rate_review",
        "base_treaty_semantic_review",
        "independent_primary_legal_review",
    }

    for row in _payload()["scopes"]:
        assert required.issubset(
            row["review_workstreams"]
        )


def test_russia_has_status_review():
    for income_type in (
        "dividend",
        "interest",
        "royalty",
    ):
        row = _scope("RU", income_type)

        assert row[
            "has_status_instrument"
        ] is True
        assert (
            row[
                "primary_review_workstream"
            ]
            == "treaty_status_instrument_review"
        )


def test_belgium_has_mli_and_protocol_review():
    row = _scope("BE", "dividend")

    assert row["has_mli_effect"] is True
    assert row["has_protocol_effect"] is True
    assert (
        "mli_ppt_and_effective_date_review"
        in row["review_workstreams"]
    )
    assert (
        "protocol_effect_review"
        in row["review_workstreams"]
    )


def test_us_interest_has_no_mli_or_protocol():
    row = _scope("US", "interest")

    assert row["has_mli_effect"] is False
    assert row["has_protocol_effect"] is False
    assert row[
        "has_status_instrument"
    ] is False


def test_at_ch_use_pilot_reconciliation():
    for country in ("AT", "CH"):
        for income_type in (
            "dividend",
            "interest",
            "royalty",
        ):
            row = _scope(
                country,
                income_type,
            )

            assert row[
                "pilot_structure_exception"
            ] is True
            assert (
                row[
                    "primary_review_workstream"
                ]
                == "pilot_structure_reconciliation"
            )


def test_hashes_are_stable():
    for row in _payload()["scopes"]:
        expected = row.pop(
            "workstream_sha256"
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


def test_summary_matches_payload():
    payload = _payload()
    summary = _summary()

    assert summary == build_summary(
        payload
    )
    assert summary["scope_count"] == 300
    assert summary["fail_closed"] is True
    assert summary[
        "approval_eligible_scopes"
    ] == 0
    assert summary["promotable_scopes"] == 0


def test_generation_is_deterministic():
    assert build_workstreams() == _payload()


import pytest


def test_priority_rejects_empty_workstreams():
    from taxtreat.tools.build_global_review_workstreams import (
        _priority,
    )

    with pytest.raises(
        ValueError,
        match="No primary review workstream assigned",
    ):
        _priority([])


def test_build_rejects_invalid_classification_count(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_review_workstreams as module

    classification_path = (
        tmp_path / "classification.json"
    )

    classification_path.write_text(
        json.dumps({
            "scopes": [],
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "CLASSIFICATION_PATH",
        classification_path,
    )

    with pytest.raises(
        ValueError,
        match="Expected 300 classified scopes",
    ):
        module.build_workstreams()


def test_build_rejects_missing_classification(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_review_workstreams as module

    original = json.loads(
        module.CLASSIFICATION_PATH.read_text(
            encoding="utf-8"
        )
    )

    classifications = original["scopes"]
    classifications[0]["packet_id"] = (
        "CZ-XX-INVALID-LEGAL-REVIEW"
    )

    classification_path = (
        tmp_path / "classification.json"
    )
    classification_path.write_text(
        json.dumps({
            **original,
            "scopes": classifications,
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "CLASSIFICATION_PATH",
        classification_path,
    )

    with pytest.raises(
        ValueError,
        match="classification missing",
    ):
        module.build_workstreams()


def test_build_rejects_wrong_pack_count(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_review_workstreams as module

    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="Expected 300 workstream rows",
    ):
        module.build_workstreams()



def test_build_rejects_duplicate_packet_ids(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_review_workstreams as module

    template = json.loads(
        next(
            module.PACKS_DIR.glob("*.json")
        ).read_text(encoding="utf-8")
    )

    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    for index in range(300):
        path = packs_dir / f"pack-{index:03d}.json"
        path.write_text(
            json.dumps(template),
            encoding="utf-8",
        )

    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        packs_dir,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate packet IDs detected",
    ):
        module.build_workstreams()

def test_build_rejects_non_fail_closed_scope(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_review_workstreams as module

    classification = json.loads(
        module.CLASSIFICATION_PATH.read_text(
            encoding="utf-8"
        )
    )

    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    original_paths = sorted(
        module.PACKS_DIR.glob("*.json")
    )

    for index, original_path in enumerate(
        original_paths
    ):
        pack = json.loads(
            original_path.read_text(
                encoding="utf-8"
            )
        )

        if index == 0:
            pack["approval_eligible"] = True

        (
            packs_dir / original_path.name
        ).write_text(
            json.dumps(pack),
            encoding="utf-8",
        )

    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        packs_dir,
    )

    with pytest.raises(
        ValueError,
        match="must remain fail-closed",
    ):
        module.build_workstreams()


def test_main_writes_outputs(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_review_workstreams as module

    output_path = (
        tmp_path / "workstreams.json"
    )
    summary_path = (
        tmp_path / "summary.json"
    )

    monkeypatch.setattr(
        module,
        "OUTPUT_PATH",
        output_path,
    )
    monkeypatch.setattr(
        module,
        "SUMMARY_PATH",
        summary_path,
    )

    module.main()

    assert output_path.exists()
    assert summary_path.exists()

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )
    summary = json.loads(
        summary_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["scope_count"] == 300
    assert summary["scope_count"] == 300
