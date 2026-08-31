from __future__ import annotations

from pathlib import Path

from taxtreat.engine.legal_rule_engine import DecisionStatus


ROOT = Path(__file__).resolve().parents[1]


def test_generic_runtime_has_no_direct_country_dispatch_for_registered_countries():
    generic_files = (
        ROOT / "taxtreat" / "engine" / "layered_decision.py",
        ROOT / "taxtreat" / "services" / "source_country_release_gate.py",
        ROOT / "taxtreat" / "services" / "source_country_runtime_metadata.py",
        ROOT / "taxtreat" / "services" / "source_country_capabilities.py",
        ROOT / "taxtreat" / "services" / "reporting" / "html_localization.py",
    )

    forbidden = (
        '== "CZ"',
        '!= "CZ"',
        '== "SK"',
        '!= "SK"',
    )

    for path in generic_files:
        text = path.read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in text, f"{path}: country dispatch leaked into core: {marker}"


def test_final_status_is_explicit_not_truthy_or_negative_review_logic():
    js = (
        ROOT
        / "app"
        / "web"
        / "workspace-output-status-integrity-20260830.js"
    ).read_text(encoding="utf-8")

    assert '=== "FINAL"' in js
    assert '!== "FINAL"' in js


def test_result_integrity_uses_backend_final_status():
    js = (
        ROOT
        / "app"
        / "web"
        / "workspace-result-integrity-20260826.js"
    ).read_text(encoding="utf-8")

    assert "analysis.status" in js
    assert "FINAL" in js


def test_report_localization_has_no_country_code_dispatch():
    text = (
        ROOT
        / "taxtreat"
        / "services"
        / "reporting"
        / "html_localization.py"
    ).read_text(encoding="utf-8")

    assert 'code == "CZ"' not in text
    assert 'code == "SK"' not in text


def test_engine_status_contract_contains_fail_closed_states():
    values = {item.value for item in DecisionStatus}

    assert "FINAL" in values
    assert "REVIEW_REQUIRED" in values
    assert "OUT_OF_SCOPE" in values
