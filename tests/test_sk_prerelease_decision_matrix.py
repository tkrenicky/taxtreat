from taxtreat.tools.validate_sk_prerelease_decision_matrix import validate_matrix


def _manifest():
    rows = []
    for i in range(75):
        country = f"X{i:02d}"
        for income in ("dividend", "interest", "royalty"):
            rows.append({
                "scope_key": ["SK", country, income],
                "source_country": "SK",
                "recipient_country": country,
                "income_type": income,
                "treaty_machine_evidence_status": "machine_candidate_not_legal_conclusion",
                "treaty_semantic_candidate": {
                    "rate_candidates": [],
                    "exclusive_residence_taxation_candidate": False,
                    "beneficial_owner_wording_present": False,
                    "pe_or_fixed_base_carveout_wording_present": False,
                    "holding_period_candidates": [],
                    "ownership_linked_rate_candidate_count": 0,
                    "evidence_quality": "official_primary_source_byte_extracted",
                },
                "mli_applicable": i < 46,
                "mli_machine_evidence_status": "completed" if i < 46 else "not_applicable",
                "mli_wht_effective_dates": ["2020-01-01"] if i < 46 else [],
                "cooperating_state_list_ready": False,
            })
    return {
        "source_country": "SK",
        "policy": {"runtime_release": False},
        "scopes": rows,
    }


def test_prerelease_decision_matrix_covers_all_225_scopes_fail_closed():
    summary = validate_matrix(_manifest())

    assert summary["schema_version"] == 2
    assert summary["scope_count"] == 225
    assert summary["evaluated_scopes"] == 225
    assert summary["review_required_scopes"] == 225
    assert summary["final_rate_scopes"] == 0
    assert summary["czech_runtime_fallback_scopes"] == 0
    assert summary["foreign_runtime_dependency_scopes"] == 0
    assert summary["production_released_scopes"] == 0
    assert summary["scopes_blocked_by_cooperating_state_list"] == 225
    assert summary["fail_closed"] is True
