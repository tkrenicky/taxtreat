from dataclasses import replace
from datetime import date
import json
from types import SimpleNamespace

import taxtreat.services.decision as decision_service
from taxtreat.countries.registry import get_country_config
from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalDecisionResult,
    TaxTreatment,
)
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    _apply_source_country_release_manifest_gate,
    analyze_transaction,
)


def _request(source_country="SK"):
    return CanonicalAnalysisRequest(
        source_country=source_country,
        recipient_country="CZ",
        income_type="dividend",
        transaction_date=date(2026, 8, 23),
        facts={},
    )


def _final_result(*, rate=10.0):
    return LegalDecisionResult(
        status=DecisionStatus.FINAL,
        requires_review=False,
        eligible=True,
        rate=rate,
        tax_treatment=TaxTreatment.TAXABLE_AT_RATE,
        selected_rule_id="RULE-1",
    )


def test_release_manifest_gate_bypasses_nonfinal_result():
    result = LegalDecisionResult(
        status=DecisionStatus.REVIEW_REQUIRED,
        requires_review=True,
    )

    assert _apply_source_country_release_manifest_gate(
        _request(), result
    ) is result


def test_release_manifest_gate_resolves_config_and_bypasses_unknown_or_no_manifest():
    unknown = _final_result()
    assert _apply_source_country_release_manifest_gate(
        _request("ZZ"), unknown
    ) is unknown

    cz = _final_result()
    assert _apply_source_country_release_manifest_gate(
        _request("CZ"), cz
    ) is cz


def test_release_manifest_gate_allows_eligible_manifest(tmp_path):
    manifest = tmp_path / "release.json"
    manifest.write_text(
        json.dumps(
            {
                "release_eligible": True,
                "release_status": "released",
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )
    config = replace(
        get_country_config("SK"),
        release_manifest_path=manifest,
    )
    result = _final_result()

    assert _apply_source_country_release_manifest_gate(
        _request(), result, country_config=config
    ) is result
    assert result.status == DecisionStatus.FINAL


def test_release_manifest_gate_invalid_manifest_fails_closed_and_preserves_candidate(tmp_path):
    manifest = tmp_path / "bad.json"
    manifest.write_text("{bad", encoding="utf-8")
    config = replace(
        get_country_config("SK"),
        release_manifest_path=manifest,
    )
    result = _final_result(rate=10.0)

    gated = _apply_source_country_release_manifest_gate(
        _request(), result, country_config=config
    )

    assert gated.status == DecisionStatus.REVIEW_REQUIRED
    assert gated.requires_review is True
    assert gated.eligible is False
    assert gated.rate is None
    assert gated.tax_treatment is None
    assert gated.selected_rule_id is None
    assert gated.candidate_rule_id == "RULE-1"
    assert gated.candidate_tax_treatment == TaxTreatment.TAXABLE_AT_RATE
    assert gated.candidate_rate == 10.0
    assert gated.missing_legal_layers == ["source_country_release_manifest"]
    assert "manifest_unavailable" in gated.explanation[-1]
    assert "source_country_release_manifest_unavailable" in gated.explanation[-1]


def test_release_manifest_gate_closed_manifest_keeps_existing_candidate_fields_and_layer(tmp_path):
    manifest = tmp_path / "closed.json"
    manifest.write_text(
        json.dumps(
            {
                "release_eligible": False,
                "release_status": "review_reopened",
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )
    config = replace(
        get_country_config("SK"),
        release_manifest_path=manifest,
    )
    result = _final_result(rate=10.0)
    result.candidate_rule_id = "CANDIDATE-RULE"
    result.candidate_tax_treatment = TaxTreatment.DOMESTIC_EXEMPTION
    result.candidate_rate = 5.0
    result.missing_legal_layers = ["source_country_release_manifest"]

    gated = _apply_source_country_release_manifest_gate(
        _request(), result, country_config=config
    )

    assert gated.candidate_rule_id == "CANDIDATE-RULE"
    assert gated.candidate_tax_treatment == TaxTreatment.DOMESTIC_EXEMPTION
    assert gated.candidate_rate == 5.0
    assert gated.missing_legal_layers == ["source_country_release_manifest"]
    assert "release_manifest_not_eligible" in gated.explanation[-1]


def test_release_manifest_gate_handles_missing_status_and_explicit_blocker(tmp_path):
    manifest = tmp_path / "closed.json"
    manifest.write_text(
        json.dumps(
            {
                "release_eligible": False,
                "blockers": ["manual_review"],
            }
        ),
        encoding="utf-8",
    )
    config = replace(
        get_country_config("SK"),
        release_manifest_path=manifest,
    )
    result = _final_result(rate=None)

    gated = _apply_source_country_release_manifest_gate(
        _request(), result, country_config=config
    )

    assert gated.candidate_rate is None
    assert "status=unknown" in gated.explanation[-1]
    assert "manual_review" in gated.explanation[-1]


def test_analyze_transaction_fails_closed_for_registered_unreleased_source(monkeypatch):
    config = replace(get_country_config("SK"), runtime_released=False)
    monkeypatch.setattr(
        decision_service,
        "get_country_config",
        lambda code: config,
    )

    result = analyze_transaction(_request())

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.requires_review is True
    assert result.eligible is False
    assert result.rate is None
    assert result.missing_legal_layers == [
        "domestic",
        "mli",
        "treaty_or_protocol",
    ]
    assert "has not been released" in result.explanation[0]


def test_analyze_transaction_uses_registered_source_rule_directory(monkeypatch, tmp_path):
    config = replace(
        get_country_config("CZ"),
        domestic_precedence_handler=None,
        rule_directory=tmp_path,
    )
    seen = {}

    monkeypatch.setattr(
        decision_service,
        "get_country_config",
        lambda code: config,
    )
    monkeypatch.setattr(
        decision_service,
        "evaluate_runtime_gate",
        lambda **kwargs: SimpleNamespace(
            applies=False,
            allowed=True,
            missing_facts=[],
            explanation=None,
        ),
    )
    monkeypatch.setattr(
        decision_service,
        "load_rule_catalog",
        lambda path: seen.setdefault("rule_dir", path) and [],
    )
    monkeypatch.setattr(
        decision_service,
        "supported_scope_keys",
        lambda **kwargs: set(),
    )

    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country="CZ",
            recipient_country="CH",
            income_type="dividend",
            transaction_date=date(2026, 8, 23),
            facts={},
        )
    )

    assert seen["rule_dir"] == tmp_path
    assert result.status == DecisionStatus.OUT_OF_SCOPE
