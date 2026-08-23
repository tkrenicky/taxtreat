from taxtreat.engine.legal_rule_engine import DecisionStatus, LegalDecisionResult
from taxtreat.services.source_country_release_gate import SourceCountryReleaseDecision


def test_simulated_released_sk_analysis_uses_only_source_country_runtime_helpers(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(
        main_module,
        "require_analysis_source_release",
        lambda source, recipient: SourceCountryReleaseDecision(
            source_country="SK",
            allowed=True,
            code="SOURCE_COUNTRY_RELEASED",
            release_status="released",
            blockers=(),
        ),
    )
    monkeypatch.setattr(
        main_module,
        "analyze_transaction",
        lambda request: LegalDecisionResult(
            status=DecisionStatus.REVIEW_REQUIRED,
            requires_review=True,
            rate=None,
            eligible=False,
            explanation=["simulated released SK runtime"],
            dataset_release="sk-rules-test",
        ),
    )

    metadata_calls = []
    calc_calls = []
    compliance_calls = []

    monkeypatch.setattr(
        main_module,
        "source_country_runtime_dataset_version",
        lambda source, **kwargs: metadata_calls.append(source) or "sk-production-test",
    )
    monkeypatch.setattr(
        main_module,
        "build_source_country_withholding_tax_calculation",
        lambda source, amount, **kwargs: calc_calls.append(source) or {
            "source_country": source,
            "status": "NOT_CALCULATED",
            "reason": "final_rate_unavailable",
        },
    )
    monkeypatch.setattr(
        main_module,
        "build_source_country_withholding_compliance_schedule",
        lambda source, transaction_date, **kwargs: compliance_calls.append(source) or {
            "source_country": source,
            "status": "PENDING_FINAL_TREATMENT",
        },
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Czech calculation/compliance helper touched by SK analysis")

    monkeypatch.setattr(main_module, "build_withholding_tax_calculation", forbidden)
    monkeypatch.setattr(main_module, "build_withholding_compliance_schedule", forbidden)

    payload = main_module.AnalysisPayload(
        source_country="SK",
        recipient_country="AT",
        income_type="interest",
        transaction_date="2026-08-19",
        facts={},
        determinations={},
        transaction_amount={"amount": "1000", "currency": "EUR"},
    )

    result = main_module.analyze(payload)

    assert metadata_calls == ["SK"]
    assert calc_calls == ["SK"]
    assert compliance_calls == ["SK"]
    assert result["dataset_version"] == "sk-production-test"
    assert result["withholding_tax_calculation"]["source_country"] == "SK"
    assert result["withholding_compliance_schedule"]["source_country"] == "SK"
