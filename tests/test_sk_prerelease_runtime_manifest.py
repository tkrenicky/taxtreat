from taxtreat.tools.build_sk_prerelease_runtime_manifest import (
    build_manifest,
    build_summary,
)


def test_prerelease_runtime_manifest_covers_all_sk_scopes_fail_closed():
    payload = build_manifest()
    summary = build_summary(payload)

    assert payload["source_country"] == "SK"
    assert payload["scope_count"] == 225
    assert len(payload["scopes"]) == 225
    assert len({tuple(row["scope_key"]) for row in payload["scopes"]}) == 225

    assert summary["scope_count"] == 225
    assert summary["mli_scopes"] == 138
    assert summary["non_mli_scopes"] == 87
    assert summary["primary_summary_fallback_scopes"] == 3
    assert summary["human_reviewed_scopes"] == 0
    assert summary["production_released_scopes"] == 0
    assert summary["fail_closed"] is True

    assert all(row["candidate_only"] is True for row in payload["scopes"])
    assert all(row["approval_eligible"] is False for row in payload["scopes"])
    assert all(row["runtime_released"] is False for row in payload["scopes"])
    assert all(row["cooperating_state_list_ready"] is False for row in payload["scopes"])


def test_prerelease_runtime_manifest_uses_only_sk_domestic_and_compliance_contracts():
    payload = build_manifest()

    assert payload["policy"]["czech_runtime_fallback_prohibited"] is True
    assert payload["policy"]["country_specific_domestic_logic_required"] is True
    assert payload["policy"]["pair_specific_mli_required"] is True
    assert payload["policy"]["runtime_release"] is False

    dividend = next(row for row in payload["scopes"] if row["income_type"] == "dividend")
    interest = next(row for row in payload["scopes"] if row["income_type"] == "interest")
    royalty = next(row for row in payload["scopes"] if row["income_type"] == "royalty")

    assert dividend["domestic_model"] == "sk_dividend_section_12_7_c"
    assert interest["domestic_model"] == "sk_interest_royalty_section_43_and_section_13"
    assert royalty["domestic_model"] == "sk_interest_royalty_section_43_and_section_13"
    assert dividend["compliance_form"] == "OZN4311v26"
    assert dividend["compliance_legal_reference"] == "§ 43 ods. 11"


def test_taiwan_fallback_remains_machine_evidence_not_release():
    payload = build_manifest()
    taiwan = [row for row in payload["scopes"] if row["recipient_country"] == "TW"]

    assert len(taiwan) == 3
    assert all("primary_summary_fallback" in row["treaty_machine_evidence_status"] for row in taiwan)
    assert all(row["candidate_only"] is True for row in taiwan)
    assert all(row["approval_eligible"] is False for row in taiwan)
    assert all(row["runtime_released"] is False for row in taiwan)
