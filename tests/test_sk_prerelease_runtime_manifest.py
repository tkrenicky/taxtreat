import json

import taxtreat.tools.build_sk_prerelease_runtime_manifest as manifest_module
from taxtreat.tools.build_sk_prerelease_runtime_manifest import (
    build_manifest,
    build_summary,
)


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_manifest_inputs(tmp_path, monkeypatch):
    countries = [f"X{i:02d}" for i in range(74)] + ["TW"]
    semantic_scopes = []
    for country in countries:
        for income in ("dividend", "interest", "royalty"):
            fallback = country == "TW"
            semantic_scopes.append({
                "packet_id": f"SK-{country}-{income}-TREATY-SOURCE",
                "recipient_country": country,
                "income_type": income,
                "semantic_status": (
                    "machine_candidate_primary_summary_fallback_not_legal_conclusion"
                    if fallback
                    else "machine_candidate_not_legal_conclusion"
                ),
                "source_url": "https://official.example/source",
                "source_sha256": None if fallback else "abc",
                "actual_article": {"dividend": "10", "interest": "11", "royalty": "12"}[income],
                "rate_candidates": [{
                    "rate_percent": 10.0,
                    "context": "candidate context",
                    "context_sha256": None if fallback else "ctx",
                    "ownership_context": income == "dividend",
                    "beneficial_owner_context": True,
                }],
                "exclusive_residence_taxation_candidate": False,
                "beneficial_owner_wording_present": True,
                "pe_or_fixed_base_carveout_wording_present": True,
                "holding_period_candidates": [],
                "ownership_linked_rate_candidate_count": 1 if income == "dividend" else 0,
                "evidence_quality": (
                    "official_primary_source_summary_fallback_not_byte_exact"
                    if fallback
                    else "official_primary_source_byte_extracted"
                ),
            })

    mli_relationships = [
        {
            "recipient_country": country,
            "machine_extraction_status": "completed",
            "slovak_notice": f"{400+i}/2020",
            "wht_effective_dates": ["2020-01-01"],
        }
        for i, country in enumerate(countries[:46])
    ]

    semantic_path = tmp_path / "semantic.json"
    mli_path = tmp_path / "mli.json"
    compliance_path = tmp_path / "compliance.json"
    dividend_path = tmp_path / "dividend.json"
    domestic_path = tmp_path / "domestic.json"
    cooperating_path = tmp_path / "cooperating.json"

    _write(semantic_path, {"scope_count": 225, "scopes": semantic_scopes})
    _write(mli_path, {"relationships": mli_relationships})
    _write(compliance_path, {
        "ordinary_corporate_outbound_wht": {
            "notification": {
                "form_code": "OZN4311v26",
                "legal_reference": "§ 43 ods. 11",
            }
        }
    })
    _write(dividend_path, {"source_country": "SK"})
    _write(domestic_path, {"source_country": "SK"})
    _write(cooperating_path, {
        "source_country": "SK",
        "official_list": {
            "valid_from": "2026-01-01",
            "valid_to": "2026-12-31",
            "mf_document_id": 49561,
        },
        "cooperating_state_codes": countries,
    })

    monkeypatch.setattr(manifest_module, "SEMANTIC_PATH", semantic_path)
    monkeypatch.setattr(manifest_module, "MLI_PATH", mli_path)
    monkeypatch.setattr(manifest_module, "COMPLIANCE_PATH", compliance_path)
    monkeypatch.setattr(manifest_module, "DIVIDEND_MODEL_PATH", dividend_path)
    monkeypatch.setattr(manifest_module, "DOMESTIC_MODEL_PATH", domestic_path)
    monkeypatch.setattr(manifest_module, "COOPERATING_SOURCE", cooperating_path)


def test_default_domestic_manifest_input_is_committed_condition_model():
    assert manifest_module.DOMESTIC_MODEL_PATH.name == "domestic_transaction_condition_model.json"
    assert manifest_module.DOMESTIC_MODEL_PATH.is_file()


def test_prerelease_runtime_manifest_covers_all_sk_scopes_fail_closed(tmp_path, monkeypatch):
    _seed_manifest_inputs(tmp_path, monkeypatch)
    payload = build_manifest()
    summary = build_summary(payload)

    assert payload["schema_version"] == 2
    assert payload["source_country"] == "SK"
    assert payload["scope_count"] == 225
    assert len(payload["scopes"]) == 225
    assert len({tuple(row["scope_key"]) for row in payload["scopes"]}) == 225

    assert summary["scope_count"] == 225
    assert summary["mli_scopes"] == 138
    assert summary["non_mli_scopes"] == 87
    assert summary["primary_summary_fallback_scopes"] == 3
    assert summary["scopes_with_rate_candidates"] == 225
    assert summary["exclusive_residence_candidate_scopes"] == 0
    assert summary["human_reviewed_scopes"] == 24
    assert summary["pattern_reconciled_scopes"] == 201
    assert summary["legal_review_covered_scopes"] == 225
    assert summary["production_released_scopes"] == 0
    assert summary["fail_closed"] is True

    assert all(row["candidate_only"] is True for row in payload["scopes"])
    assert all(row["approval_eligible"] is False for row in payload["scopes"])
    assert all(row["runtime_released"] is False for row in payload["scopes"])
    assert all(row["cooperating_state_list_ready"] is True for row in payload["scopes"])


def test_prerelease_runtime_manifest_carries_treaty_semantics_without_approval(tmp_path, monkeypatch):
    _seed_manifest_inputs(tmp_path, monkeypatch)
    payload = build_manifest()

    dividend = next(row for row in payload["scopes"] if row["income_type"] == "dividend")
    semantic = dividend["treaty_semantic_candidate"]

    assert semantic["rate_candidates"][0]["rate_percent"] == 10.0
    assert semantic["beneficial_owner_wording_present"] is True
    assert semantic["pe_or_fixed_base_carveout_wording_present"] is True
    assert semantic["ownership_linked_rate_candidate_count"] == 1
    assert payload["policy"]["semantic_candidates_must_never_be_promoted_without_human_review"] is True
    assert dividend["approval_eligible"] is False
    assert dividend["runtime_released"] is False


def test_prerelease_runtime_manifest_uses_only_sk_domestic_and_compliance_contracts(tmp_path, monkeypatch):
    _seed_manifest_inputs(tmp_path, monkeypatch)
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


def test_taiwan_fallback_remains_machine_evidence_not_release(tmp_path, monkeypatch):
    _seed_manifest_inputs(tmp_path, monkeypatch)
    payload = build_manifest()
    taiwan = [row for row in payload["scopes"] if row["recipient_country"] == "TW"]

    assert len(taiwan) == 3
    assert all("primary_summary_fallback" in row["treaty_machine_evidence_status"] for row in taiwan)
    assert all(
        row["treaty_semantic_candidate"]["evidence_quality"]
        == "official_primary_source_summary_fallback_not_byte_exact"
        for row in taiwan
    )
    assert all(row["candidate_only"] is True for row in taiwan)
    assert all(row["approval_eligible"] is False for row in taiwan)
    assert all(row["runtime_released"] is False for row in taiwan)
