from taxtreat.tools.apply_sk_pass2_runtime_fixes import build_integrated_main


BASE = '''from taxtreat.services.calculation import (
    build_withholding_compliance_schedule,
    build_withholding_tax_calculation,
)

def require_analysis_source_release(source_country, recipient_country):
    source = source_country.upper()
    recipient = recipient_country.upper()

    if source != "CZ":
        try:
            require_source_country_analysis_release(source)
        except UnsupportedSourceCountryError as exc:
            raise HTTPException(status_code=422) from exc
        except SourceCountryNotReleasedError as exc:
            raise HTTPException(status_code=409) from exc
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SOURCE_COUNTRY_RELEASE_GATE_MISSING",
                "source_country": source,
            },
        )

    treaty_pair_id = f"{source}-{recipient}"

def analyze(payload):
    source_country = payload.source_country.upper()
    amount = None
    result = object()
    calculation = build_withholding_tax_calculation(
        amount,
        decision_status=result.status.value,
        rate_percent=result.rate,
        tax_treatment=None,
    )
    schedule = (
        build_withholding_compliance_schedule(
            payload.transaction_date,
            income_type=payload.income_type,
            decision_status=result.status.value,
            rate_percent=result.rate,
        )
    )
'''


def test_patcher_removes_non_cz_fallthrough_and_routes_calculation_by_source_country():
    patched = build_integrated_main(BASE)

    assert "return require_source_country_analysis_release(source)" in patched
    assert "SOURCE_COUNTRY_RELEASE_GATE_MISSING" not in patched
    assert "build_source_country_withholding_tax_calculation(\n        source_country," in patched
    assert "build_source_country_withholding_compliance_schedule(\n            source_country," in patched


def test_patcher_is_idempotent():
    once = build_integrated_main(BASE)
    twice = build_integrated_main(once)
    assert twice == once
