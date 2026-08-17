from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Missing marker {label} in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    main_py = ROOT / "app" / "main.py"
    old = '''    return {"total": len(jurisdictions), "jurisdictions": jurisdictions}\n\n\ndef require_analysis_source_release'''
    new = '''    # Taiwan is supported by the production runtime through Czech domestic\n    # withholding-tax rules even though it is not a Czech treaty partner.\n    # `/jurisdictions` is a product-support catalog, not merely a treaty list.\n    jurisdictions.append(\n        {\n            "country": "Tchaj-wan",\n            "iso2": "TW",\n            "income_types": ["dividend", "interest", "royalty"],\n            "review_ready_income_types": [],\n            "base_candidate_income_types": [],\n            "protocol_candidate_income_types": [],\n            "domestic_candidate_income_types": ["dividend", "interest", "royalty"],\n            "eu_relief_candidate_income_types": [],\n            "manual_rate_extraction_income_types": [],\n            "candidate_chain_assembled_income_types": [],\n            "candidate_chain_blocked_income_types": [],\n            "candidate_review_queued_income_types": [],\n            "candidate_review_approved_income_types": [],\n        }\n    )\n    return {"total": len(jurisdictions), "jurisdictions": jurisdictions}\n\n\ndef require_analysis_source_release'''
    replace_once(main_py, old, new, "jurisdictions return")

    js = ROOT / "app" / "web" / "workspace.js"
    text = js.read_text(encoding="utf-8")
    text = text.replace(
        'if (analysis.candidate_rate !== null && analysis.candidate_rate !== undefined) return `Byla identifikována sazba ${analysis.candidate_rate} %. Její použití závisí na odborném ověření právních podmínek uvedených níže.`;',
        'if (analysis.candidate_rate !== null && analysis.candidate_rate !== undefined) return `Byla identifikována sazba ${analysis.candidate_rate} %. Její použití závisí na splnění právních a skutkových podmínek uvedených níže.`;',
    )
    text = text.replace(
        'return "Sazbu zatím nelze určit. Konkrétní důvod je uveden v části Odborné ověření níže.";',
        'return "Sazbu zatím nelze určit. Konkrétní důvod je uveden v části Podmínky a další kroky níže.";',
    )
    js.write_text(text, encoding="utf-8")

    test = ROOT / "tests" / "test_ares_company_registry.py"
    existing = test.read_text(encoding="utf-8")
    existing += '''\n\ndef test_jurisdiction_catalog_contains_all_supported_destinations():\n    from fastapi.testclient import TestClient\n    from app.main import app\n\n    response = TestClient(app).get("/jurisdictions")\n    assert response.status_code == 200\n    body = response.json()\n    assert body["total"] == 101\n    codes = {item["iso2"] for item in body["jurisdictions"]}\n    assert len(codes) == 101\n    assert "KR" in codes\n    assert "TW" in codes\n'''
    test.write_text(existing, encoding="utf-8")

    browser = ROOT / "scripts" / "check_workspace_report_export.py"
    content = browser.read_text(encoding="utf-8")
    marker = '''    if country.locator("option").count() != 102:\n        raise AssertionError("Recipient form does not expose all 101 jurisdictions.")\n'''
    replacement = '''    if country.locator("option").count() != 102:\n        raise AssertionError("Recipient form does not expose all 101 jurisdictions.")\n    option_values = country.locator("option").evaluate_all("options => options.map(option => option.value)")\n    if "KR" not in option_values or "TW" not in option_values:\n        raise AssertionError("Recipient catalog must include both Korea and Taiwan.")\n'''
    if marker not in content:
        raise RuntimeError("Browser jurisdiction assertion marker missing")
    browser.write_text(content.replace(marker, replacement, 1), encoding="utf-8")
    print("Supported jurisdiction catalog fixed.")


if __name__ == "__main__":
    main()
