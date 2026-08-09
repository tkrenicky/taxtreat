from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from taxtreat.consolidation.instrument_chains import (
    _mli_status,
    build_instrument_chains,
    write_instrument_chains,
)


ROOT = Path(__file__).parents[1]
DATASET = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "remaining_294_instrument_chains.json"
)


def _payload():
    return json.loads(DATASET.read_text(encoding="utf-8"))


def _scope(country: str, income_type: str):
    return next(
        row
        for row in _payload()["scopes"]
        if row["recipient_country"] == country
        and row["income_type"] == income_type
    )


def test_candidate_chains_cover_all_remaining_scopes_fail_closed():
    payload = _payload()
    scopes = payload["scopes"]

    assert len(scopes) == 294
    assert len({row["recipient_country"] for row in scopes}) == 98
    assert {row["recipient_country"] for row in scopes}.isdisjoint({"AT", "CH"})
    assert payload["summary"] == {
        "blocked_partners": 0,
        "candidate_chain_assembled_scopes": 294,
        "candidate_chain_blocked_scopes": 0,
        "review_ready_scopes": 0,
        "total_scopes": 294,
        "verified_scopes": 0,
    }
    assert all(
        row["verification_status"] == "needs_review"
        and row["review_ready"] is False
        and "independent_legal_review" in row["legal_review_tasks"]
        for row in scopes
    )


def test_hard_blocker_queue_is_exact_and_country_specific():
    assert _payload()["blocker_queue"] == []
    assert all(not row["hard_blockers"] for row in _payload()["scopes"])


def test_chain_keeps_layers_separate_and_does_not_choose_a_final_rate():
    germany = _scope("DE", "dividend")

    assert germany["chain_status"] == "candidate_chain_assembled"
    assert germany["base_treaty"]["candidate_rates"] == [5.0, 15.0, 20.0]
    assert germany["czech_domestic_law"]["standard_rate"] == 15.0
    assert germany["czech_domestic_law"]["protective_rate"] == 35.0
    assert germany["section_19_relief"]["candidate_rate"] == 0.0
    assert germany["mli"]["effective_from"] == "2026-01-01"
    assert "semantic_rate_review" in germany["legal_review_tasks"]
    assert "final_rate" not in germany


def test_former_blockers_are_resolved_without_activating_rules():
    greek = _scope("GR", "dividend")
    assert greek["base_treaty"]["candidate_rates"] == []
    assert greek["base_treaty"]["treaty_rate_cap_status"] == "no_numeric_cap"
    assert greek["base_treaty"]["source_state_taxation_candidate"][
        "source_state_taxation"
    ] == "permitted_under_domestic_law"

    assert _scope("EE", "interest")["mli"]["effective_from"] == "2025-01-01"
    assert _scope("SE", "royalty")["mli"]["effective_from"] == "2021-01-01"
    assert _scope("CO", "royalty")["mli"]["status"] == (
        "signed_not_ratified_no_current_wht_effect"
    )

    assert _scope("BY", "dividend")["treaty_status_instrument"][
        "candidate_status"
    ] == "article_application_suspended"
    assert _scope("BY", "royalty")["treaty_status_instrument"][
        "candidate_status"
    ] == "article_not_suspended_by_notice"
    assert _scope("RU", "royalty")["treaty_status_instrument"][
        "candidate_status"
    ] == "article_application_suspended"
    assert all(
        row["verification_status"] == "needs_review"
        and row["review_ready"] is False
        for row in (greek, _scope("EE", "interest"), _scope("RU", "royalty"))
    )


def test_candidate_hashes_and_generation_are_deterministic():
    payload = _payload()

    # The committed legacy snapshot must remain internally
    # hash-consistent because existing legal-review packets
    # reference these hashes.
    for scope in payload["scopes"]:
        expected = scope["candidate_sha256"]

        unhashed = dict(scope)
        unhashed.pop("candidate_sha256")

        actual = hashlib.sha256(
            json.dumps(
                unhashed,
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        assert actual == expected

    generated = build_instrument_chains()

    boundary = json.loads(
        (
            ROOT
            / "data"
            / "legal_consolidation"
            / "final23_migration_boundary.json"
        ).read_text(encoding="utf-8")
    )

    migrated = set(
        boundary["migrated_recipient_countries"]
    )

    def indexed(value):
        return {
            (
                scope["source_country"],
                scope["recipient_country"],
                scope["income_type"],
            ): scope
            for scope in value["scopes"]
        }

    committed_scopes = indexed(payload)
    generated_scopes = indexed(generated)

    assert (
        set(committed_scopes)
        == set(generated_scopes)
    )

    drifted = {
        key
        for key in committed_scopes
        if (
            committed_scopes[key]
            != generated_scopes[key]
        )
    }

    # Zero drift is fully valid. If generator drift exists,
    # it may only affect scopes migrated to the dedicated
    # Final23 candidate workflow.
    assert all(
        recipient in migrated
        for _, recipient, _ in drifted
    )

    # Everything outside Final23 remains strictly
    # deterministic against the committed snapshot.
    for key in committed_scopes:
        if key[1] in migrated:
            continue

        assert (
            committed_scopes[key]
            == generated_scopes[key]
        )


def test_builder_rejects_missing_base_scope(tmp_path):
    source = json.loads(
        (
            ROOT
            / "data"
            / "legal_consolidation"
            / "remaining_294_base_candidates.json"
        ).read_text(encoding="utf-8")
    )
    source["scopes"].pop()
    target = tmp_path / "base.json"
    target.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="Expected 294"):
        build_instrument_chains(base_candidates_path=target)


def test_builder_rejects_duplicate_base_scope(tmp_path):
    source = json.loads(
        (
            ROOT
            / "data"
            / "legal_consolidation"
            / "remaining_294_base_candidates.json"
        ).read_text(encoding="utf-8")
    )
    source["scopes"][-1] = source["scopes"][0]
    target = tmp_path / "base.json"
    target.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate base-treaty"):
        build_instrument_chains(base_candidates_path=target)


@pytest.mark.parametrize(
    ("filename", "field", "match"),
    [
        ("mf_inventory.json", "partners", "cover 100 partners"),
        ("mli_wht_effects.json", "effects", "cover 62 partners"),
    ],
)
def test_builder_rejects_incomplete_partner_registries(
    tmp_path,
    filename,
    field,
    match,
):
    source = json.loads(
        (ROOT / "data" / "legal_consolidation" / filename).read_text(
            encoding="utf-8"
        )
    )
    source[field].pop()
    target = tmp_path / filename
    target.write_text(json.dumps(source), encoding="utf-8")
    kwargs = (
        {"inventory_path": target}
        if filename == "mf_inventory.json"
        else {"mli_effects_path": target}
    )

    with pytest.raises(ValueError, match=match):
        build_instrument_chains(**kwargs)


def test_builder_rejects_scope_drift_in_layer_registries(tmp_path):
    consolidation = ROOT / "data" / "legal_consolidation"

    base = json.loads(
        (consolidation / "remaining_294_base_candidates.json").read_text(
            encoding="utf-8"
        )
    )
    base["scopes"][0]["recipient_country"] = "AT"
    base_target = tmp_path / "base.json"
    base_target.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="do not match"):
        build_instrument_chains(base_candidates_path=base_target)

    protocol = json.loads(
        (consolidation / "protocol_effect_candidates.json").read_text(
            encoding="utf-8"
        )
    )
    protocol["scopes"][0]["recipient_country"] = "AT"
    protocol_target = tmp_path / "protocol.json"
    protocol_target.write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(ValueError, match="outside the baseline"):
        build_instrument_chains(protocol_effects_path=protocol_target)

    domestic = json.loads(
        (consolidation / "cz_domestic_eu_candidates.json").read_text(
            encoding="utf-8"
        )
    )
    target_scope = next(
        row
        for row in domestic["scopes"]
        if row["recipient_country"] == "DE" and row["income_type"] == "dividend"
    )
    target_scope["recipient_country"] = "ZZ"
    domestic_target = tmp_path / "domestic.json"
    domestic_target.write_text(json.dumps(domestic), encoding="utf-8")
    with pytest.raises(ValueError, match="do not cover"):
        build_instrument_chains(domestic_eu_path=domestic_target)


def test_missing_required_protocol_reopens_the_completed_chain_gate(tmp_path):
    source = json.loads(
        (
            ROOT
            / "data"
            / "legal_consolidation"
            / "protocol_effect_candidates.json"
        ).read_text(encoding="utf-8")
    )
    target_scope = next(
        row
        for row in source["scopes"]
        if row["recipient_country"] == "BY" and row["income_type"] == "dividend"
    )
    target_scope["recipient_country"] = "DE"
    target = tmp_path / "protocol.json"
    target.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="found 293 and 1"):
        build_instrument_chains(protocol_effects_path=target)


@pytest.mark.parametrize(
    ("field", "match"),
    [
        ("mli_resolutions", "cover 9 partners"),
        ("status_instruments", "cover BY and RU"),
        ("base_treaty_resolutions", "cover Greek dividends"),
    ],
)
def test_builder_rejects_incomplete_blocker_resolutions(tmp_path, field, match):
    source = json.loads(
        (
            ROOT
            / "data"
            / "legal_consolidation"
            / "blocker_resolutions.json"
        ).read_text(encoding="utf-8")
    )
    source[field].pop()
    target = tmp_path / "blocker_resolutions.json"
    target.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match=match):
        build_instrument_chains(blocker_resolutions_path=target)


def test_writer_round_trip(tmp_path):
    target = tmp_path / "nested" / "chains.json"
    payload = build_instrument_chains()
    write_instrument_chains(payload, target)

    assert json.loads(target.read_text(encoding="utf-8")) == payload


def test_unresolved_mli_status_branches_remain_fail_closed():
    assert _mli_status(
        {"mli_listed": False, "mli_notice_available": False}, None, None
    ) == "not_listed"
    assert _mli_status(
        {"mli_listed": True, "mli_notice_available": True}, None, None
    ) == "official_notice_requires_wht_effect_extraction"
    assert _mli_status(
        {"mli_listed": True, "mli_notice_available": False}, None, None
    ) == "matching_and_effective_date_required"
