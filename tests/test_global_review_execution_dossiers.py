from __future__ import annotations

import hashlib
import json
from pathlib import Path

from taxtreat.tools.build_global_review_execution_dossiers import (
    build_execution_dossiers,
    build_summary,
)


ROOT = Path(__file__).parents[1]

GLOBAL_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

INDEX_PATH = (
    GLOBAL_DIR
    / "global_review_execution_dossiers.json"
)

SUMMARY_PATH = (
    GLOBAL_DIR
    / "global_review_execution_dossiers_summary.json"
)

DOSSIERS_DIR = (
    GLOBAL_DIR
    / "execution_dossiers"
)


def _payload():
    return json.loads(
        INDEX_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_all_batches_have_dossiers():
    payload = _payload()

    assert payload["batch_count"] == 23
    assert payload["scope_count"] == 300
    assert payload["country_count"] == 100
    assert len(payload["dossiers"]) == 23


def test_all_dossier_files_exist():
    for row in _payload()["dossiers"]:
        assert (
            DOSSIERS_DIR / row["file"]
        ).exists()


def test_all_scopes_are_fail_closed():
    packet_ids = []

    for index_row in _payload()["dossiers"]:
        dossier = json.loads(
            (
                DOSSIERS_DIR
                / index_row["file"]
            ).read_text(encoding="utf-8")
        )

        assert dossier[
            "approval_eligible"
        ] is False
        assert dossier[
            "promotable_to_active_rules"
        ] is False

        for scope in dossier[
            "scope_dossiers"
        ]:
            packet_ids.append(
                scope["packet_id"]
            )

            assert scope[
                "primary_review_status"
            ] == "not_started"
            assert scope[
                "independent_approval_status"
            ] == "not_started"
            assert scope[
                "approval_eligible"
            ] is False
            assert scope[
                "promotable_to_active_rules"
            ] is False

    assert len(packet_ids) == 300
    assert len(set(packet_ids)) == 300


def test_every_scope_has_review_tasks():
    for index_row in _payload()["dossiers"]:
        dossier = json.loads(
            (
                DOSSIERS_DIR
                / index_row["file"]
            ).read_text(encoding="utf-8")
        )

        for scope in dossier[
            "scope_dossiers"
        ]:
            assert scope["review_tasks"]

            assert all(
                task["status"]
                == "not_started"
                and task["reviewer"] is None
                and task["conclusion"] is None
                for task in scope[
                    "review_tasks"
                ]
            )


def test_summary_matches_payload():
    payload = _payload()
    summary = json.loads(
        SUMMARY_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert build_summary(payload) == summary
    assert summary[
        "ready_for_primary_review_batches"
    ] == 23
    assert summary[
        "approval_eligible_scopes"
    ] == 0
    assert summary["promotable_scopes"] == 0


def test_generation_is_deterministic():
    assert (
        build_execution_dossiers()
        == _payload()
    )


def test_index_hashes_match_files():
    for row in _payload()["dossiers"]:
        dossier = json.loads(
            (
                DOSSIERS_DIR
                / row["file"]
            ).read_text(encoding="utf-8")
        )

        expected = dossier.pop(
            "dossier_sha256"
        )

        actual = hashlib.sha256(
            json.dumps(
                dossier,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        assert actual == expected
        assert row[
            "dossier_sha256"
        ] == expected
