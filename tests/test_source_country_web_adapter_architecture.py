from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "app" / "web" / "source-country-context.js"
ADAPTER = ROOT / "app" / "web" / "workspace-source-country-adapter.js"
SK_BACKEND = ROOT / "taxtreat" / "countries" / "sk.py"


def test_country_profile_contains_reusable_workspace_metadata():
    text = CONTEXT.read_text(encoding="utf-8")

    for field in [
        "taxResultLabel",
        "taxResultLabelWithCurrency",
        "complianceTitle",
        "remittanceLabel",
        "notificationLabel",
        "sourceMetrics",
        "hideWorkspaceFxControls",
        "prohibitedFxServicePrefixes",
        "interestMonthlyAmountFieldVisible",
        "payerSubtitle",
        "metaDescription",
        "prereleaseNotice",
        "complianceNoteDefault",
        "peLocationLabel",
        "payerGenitiveLabel",
    ]:
        assert field in text


def test_workspace_adapter_no_longer_branches_on_sk_code():
    text = ADAPTER.read_text(encoding="utf-8")

    assert 'ctx.code === "SK"' not in text
    assert 'currentCode === "SK"' not in text
    assert 'currentCode !== "SK"' not in text


def test_workspace_adapter_uses_country_profile_for_metrics():
    text = ADAPTER.read_text(encoding="utf-8")

    assert "ctx.sourceMetrics" in text
    assert "metrics.jurisdictionLabel" in text
    assert "metrics.scopeValue" in text


def test_workspace_adapter_uses_country_profile_for_fx_policy():
    text = ADAPTER.read_text(encoding="utf-8")

    assert "ctx.hideWorkspaceFxControls" in text
    assert "ctx.prohibitedFxServicePrefixes" in text
    assert "prohibitedPrefixes.some" in text


def test_workspace_adapter_uses_country_profile_for_copy():
    text = ADAPTER.read_text(encoding="utf-8")

    assert "ctx.taxResultLabelWithCurrency" in text
    assert "ctx.taxResultLabel" in text
    assert "ctx.complianceTitle" in text
    assert "ctx.remittanceLabel" in text
    assert "ctx.notificationLabel" in text
    assert "ctx.payerSubtitle" in text
    assert "ctx.metaDescription" in text


def test_public_web_exposes_released_sk_through_generic_adapter():
    context = CONTEXT.read_text(encoding="utf-8")
    adapter = ADAPTER.read_text(encoding="utf-8")
    backend = SK_BACKEND.read_text(encoding="utf-8")

    assert 'SK: Object.freeze({' in context
    assert '<option value="SK">Slovensko</option>' in adapter
    assert 'countryControl.hidden = true;' not in adapter
    assert 'ctx.code === "SK"' not in adapter

    assert 'def evaluate_domestic_precedence(' in backend
    assert 'OUTSIDE_SUBJECT_OF_TAX' in backend
