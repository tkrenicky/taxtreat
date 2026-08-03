from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from taxtreat.consolidation.protocol_effects import build_protocol_effects


ROOT = Path(__file__).parents[1]
PROTOCOL_EFFECTS = (
    ROOT / "data" / "legal_consolidation" / "protocol_effect_candidates.json"
)


def _payload():
    return json.loads(PROTOCOL_EFFECTS.read_text(encoding="utf-8"))


def _scope(country: str, income_type: str):
    return next(
        row
        for row in _payload()["scopes"]
        if row["recipient_country"] == country
        and row["income_type"] == income_type
    )


def test_protocol_dataset_covers_every_non_pilot_protocol_scope():
    payload = _payload()

    assert len(payload["documents"]) == 12
    assert len(payload["scopes"]) == 33
    assert len({row["recipient_country"] for row in payload["scopes"]}) == 11
    assert {
        (row["recipient_country"], row["income_type"])
        for row in payload["scopes"]
    } == {
        (country, income_type)
        for country in {row["recipient_country"] for row in payload["scopes"]}
        for income_type in {"dividend", "interest", "royalty"}
    }
    assert all(
        row["verification_status"] == "needs_review"
        for row in payload["scopes"]
    )
    assert all(
        len(document["source_document_sha256"]) == 64
        and document["url"].startswith("https://")
        for document in payload["documents"]
    )


def test_protocol_scope_candidate_hashes_are_stable():
    for scope in _payload()["scopes"]:
        expected = scope.pop("candidate_sha256")
        actual = hashlib.sha256(
            json.dumps(scope, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        assert actual == expected


def test_protocol_generation_is_deterministic():
    assert build_protocol_effects() == _payload()


def test_known_protocol_rate_changes_are_structured_not_inferred():
    assert {
        row["rate"] for row in _scope("BY", "dividend")["protocol_rate_candidates"]
    } == {5.0, 10.0}
    assert {
        row["rate"] for row in _scope("RU", "interest")["protocol_rate_candidates"]
    } == {0.0}
    assert {
        row["rate"] for row in _scope("SG", "royalty")["protocol_rate_candidates"]
    } == {0.0, 5.0, 10.0}
    assert {
        row["rate"] for row in _scope("UZ", "dividend")["protocol_rate_candidates"]
    } == {5.0, 10.0}


def test_later_belarus_and_russia_status_instruments_remain_blocking():
    for country in ("BY", "RU"):
        for income_type in ("dividend", "interest", "royalty"):
            scope = _scope(country, income_type)
            assert scope["later_status_source_id"]
            assert (
                "post_protocol_status_instrument_consolidation"
                in scope["consolidation_blockers"]
            )


def test_builder_rejects_incomplete_protocol_inventory(tmp_path):
    inventory = json.loads(
        (ROOT / "data" / "legal_consolidation" / "mf_inventory.json")
        .read_text(encoding="utf-8")
    )
    inventory["partners"] = [
        row for row in inventory["partners"] if row["iso2"] != "UZ"
    ]
    target = tmp_path / "inventory.json"
    target.write_text(json.dumps(inventory), encoding="utf-8")

    with pytest.raises(ValueError, match="coverage must match"):
        build_protocol_effects(inventory_path=target)
