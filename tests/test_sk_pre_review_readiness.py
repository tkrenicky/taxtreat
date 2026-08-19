from __future__ import annotations

from taxtreat.tools.build_sk_pre_review_readiness import build_readiness


def test_pre_review_dashboard_preserves_full_scope_and_human_review_policy():
    payload = build_readiness()

    assert payload["source_country"] == "SK"
    assert payload["target"]["country_relationships"] == 75
    assert payload["target"]["treaty_scopes"] == 225
    assert payload["target"]["mli_relationships"] == 46
    assert payload["machine_preparation"]["scopes"] == 225

    assert payload["human_review"]["started"] is False
    assert payload["human_review"]["reviewed_scopes"] == 0
    assert payload["runtime"]["released"] is False
    assert payload["runtime"]["production_released_scopes"] == 0
    assert payload["fail_closed"] is True


def test_pre_review_dashboard_blocks_until_2026_cooperating_list_is_ingested():
    payload = build_readiness()

    assert payload["domestic"]["cooperating_state_list_ingestion_complete"] is False
    assert "official_2026_cooperating_state_list_body_not_ingested" in payload["blockers"]
    assert payload["all_machine_evidence_ready"] is False
    assert payload["human_review"]["may_start"] is False


def test_mli_instrument_chain_has_no_unexplained_silent_notice_replacement():
    payload = build_readiness()
    chain = payload["mli_instrument_chain"]

    assert chain["relationships"] == 46
    assert chain["resolved_relationships"] + chain["unresolved_notice_mismatches"] == 46
