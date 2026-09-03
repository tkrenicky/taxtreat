from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_cz_sk_combinatorial_web_qa.py"
WORKFLOW = ROOT / ".github" / "workflows" / "cz-sk-combinatorial-web-qa.yml"


def test_combinatorial_gate_is_condition_derived_and_covers_both_sources():
    text = SCRIPT.read_text(encoding="utf-8")

    assert '"CZ": ROOT / "data" / "legal_rules_stage6"' in text
    assert '"SK": ROOT / "data" / "legal_rules_sk"' in text
    assert "scope_conditions" in text
    assert "condition_values" in text
    assert "boundary_or_fail" in text
    assert "MIN_EXPECTED_SCENARIOS = 3000" in text


def test_combinatorial_gate_traverses_analysis_intake_and_report():
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'client.post("/analysis", json=payload)' in text
    assert 'client.post(f"/analysis/intake?lang={lang}", json=payload)' in text
    assert 'client.post("/analysis/report", json=report_payload)' in text
    assert "intake_analysis_divergence" in text
    assert "nondeterministic_analysis" in text


def test_combinatorial_gate_contains_real_web_visible_variants():
    text = SCRIPT.read_text(encoding="utf-8")

    for marker in (
        "treaty_resident_false",
        "beneficial_owner_false",
        "pe_connection_true",
        "ownership_10",
        "ownership_25",
        "holding_12m",
        "arm_length_false",
        '"computer_software"',
        '"industrial_ip_knowhow"',
        '"other"',
    ):
        assert marker in text


def test_combinatorial_workflow_runs_full_report_enabled_gate():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "run_cz_sk_combinatorial_web_qa.py" in text
    assert "--skip-reports" not in text
    assert "timeout-minutes: 45" in text
    assert "upload-artifact@v4" in text
