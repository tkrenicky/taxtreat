from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from taxtreat.consolidation import blocker_resolutions
from taxtreat.consolidation.blocker_resolutions import (
    build_blocker_resolutions,
    write_blocker_resolutions,
)


ROOT = Path(__file__).parents[1]
DATASET = ROOT / "data" / "legal_consolidation" / "blocker_resolutions.json"
INVENTORY = ROOT / "data" / "legal_consolidation" / "mf_inventory.json"


def _payload():
    return json.loads(DATASET.read_text(encoding="utf-8"))


def test_blocker_resolution_dataset_is_complete_and_fail_closed():
    payload = _payload()

    assert payload["legal_status_as_of"] == "2026-08-04"
    assert payload["verification_status"] == "needs_review"
    assert payload["summary"] == {
        "base_treaty_semantic_resolutions": 1,
        "mli_effect_candidates": 2,
        "mli_no_current_effect_determinations": 7,
        "resolved_scopes": 34,
        "status_instruments": 2,
    }
    assert {row["recipient_country"] for row in payload["mli_resolutions"]} == {
        "CO", "EE", "IT", "KW", "MA", "MK", "NG", "SE", "TR"
    }
    assert all(
        hashlib.sha256(row["evidence"]["summary"].encode()).hexdigest()
        == row["evidence"]["summary_sha256"]
        for group in (
            payload["mli_resolutions"],
            payload["status_instruments"],
            payload["base_treaty_resolutions"],
        )
        for row in group
    )
    assert all(
        row["url"].startswith("https://www.oecd.org/")
        for row in payload["source_documents"]
    )


def test_mli_effect_and_non_effect_dates_are_explicit():
    by_code = {row["recipient_country"]: row for row in _payload()["mli_resolutions"]}

    assert by_code["EE"]["effective_from"] == "2025-01-01"
    assert by_code["SE"]["effective_from"] == "2021-01-01"
    assert by_code["TR"]["deposit_of_ratification"] is None
    assert by_code["TR"]["checked_as_of"] == "2026-08-04"
    assert by_code["TR"]["resolution_status"] == (
        "signed_not_ratified_no_current_wht_effect"
    )


def test_status_instrument_scope_is_article_specific():
    by_code = {
        row["recipient_country"]: row
        for row in _payload()["status_instruments"]
    }

    assert by_code["BY"]["effective_from"] == "2024-06-01"
    assert by_code["BY"]["effective_to"] == "2026-12-31"
    assert by_code["BY"]["suspended_articles"] == [10, 11, 13]
    assert 12 not in by_code["BY"]["suspended_articles"]
    assert by_code["RU"]["effective_from"] == "2023-08-11"
    assert by_code["RU"]["effective_to"] is None
    assert {10, 11, 12}.issubset(by_code["RU"]["suspended_articles"])


def test_builder_is_deterministic_and_writer_round_trips(tmp_path):
    assert build_blocker_resolutions() == _payload()
    target = tmp_path / "nested" / "resolutions.json"
    write_blocker_resolutions(_payload(), target)
    assert json.loads(target.read_text(encoding="utf-8")) == _payload()


def test_builder_rejects_missing_status_source(tmp_path):
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    belarus = next(row for row in inventory["partners"] if row["iso2"] == "BY")
    belarus["related_instruments"] = [
        row
        for row in belarus["related_instruments"]
        if row["source_id"] != "CZ-MF-BY-852FD44A9622"
    ]
    target = tmp_path / "inventory.json"
    target.write_text(json.dumps(inventory), encoding="utf-8")

    with pytest.raises(ValueError, match="Missing status source"):
        build_blocker_resolutions(inventory_path=target)


def test_builder_rejects_incomplete_inventory(tmp_path):
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    inventory["partners"].pop()
    target = tmp_path / "inventory.json"
    target.write_text(json.dumps(inventory), encoding="utf-8")

    with pytest.raises(ValueError, match="cover 100 partners"):
        build_blocker_resolutions(inventory_path=target)


def test_builder_rejects_mli_resolution_for_unlisted_partner(tmp_path):
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    colombia = next(
        row for row in inventory["partners"] if row["iso2"] == "CO"
    )
    colombia["mli_listed"] = False
    target = tmp_path / "inventory.json"
    target.write_text(json.dumps(inventory), encoding="utf-8")

    with pytest.raises(ValueError, match="not listed for MLI"):
        build_blocker_resolutions(inventory_path=target)


def test_builder_rejects_drift_in_expected_mli_queue(monkeypatch):
    monkeypatch.setattr(
        blocker_resolutions,
        "MLI_RESOLUTIONS",
        blocker_resolutions.MLI_RESOLUTIONS[:-1],
    )

    with pytest.raises(ValueError, match="expected queue"):
        blocker_resolutions.build_blocker_resolutions()
