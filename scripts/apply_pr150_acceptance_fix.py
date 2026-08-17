from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Missing expected marker in {path}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    replace(
        "tests/test_app.py",
        '    assert payload["total"] == 100\n    by_code = {row["iso2"]: row for row in payload["jurisdictions"]}\n    assert len(by_code) == 100\n',
        '    assert payload["total"] == 101\n    by_code = {row["iso2"]: row for row in payload["jurisdictions"]}\n    assert len(by_code) == 101\n    assert "KR" in by_code\n    assert "TW" in by_code\n',
    )

    replace(
        "tests/test_stage7a_calculation.py",
        '    assert response.status_code == 200\n    assert "final_rate_unavailable" in response.json()["html"]\n',
        '    assert response.status_code == 200\n    payload = response.json()\n    calculation = payload["report"]["result"]["withholding_tax_calculation"]\n    assert calculation["reason"] == "final_rate_unavailable"\n    assert "final_rate_unavailable" not in payload["html"]\n    assert "Výsledek vyžaduje doplnění údajů" in payload["html"]\n',
    )

    replace(
        "tests/test_stage7a_reporting.py",
        '    assert "Není právním nebo daňovým poradenstvím" in report["disclaimer"]\n    assert "<!doctype html>" in payload["html"]\n    assert report["report_id"] in payload["html"]\n',
        '    assert "nepředstavuje právní ani daňové poradenství" in report["disclaimer"]\n    assert "<!doctype html>" in payload["html"]\n    assert report["report_id"] not in payload["html"]\n',
    )
    replace(
        "tests/test_stage7a_reporting.py",
        '    assert "uvolněného katalogu" in final["risk_assessment"]\n',
        '    assert "právních pravidel uvedených v tomto výstupu" in final["risk_assessment"]\n',
    )

    replace(
        "tests/test_stage7b_ui.py",
        '    assert "Odborné ověření" in html\n',
        '    assert "Podmínky a další kroky" in html\n    assert "Odborné ověření" not in html\n',
    )
    for old, new in (
        ('/ui-assets/workspace.css?v=20260815-11', '/ui-assets/workspace.css?v=20260817-1'),
        ('/ui-assets/workspace.js?v=20260815-11', '/ui-assets/workspace.js?v=20260817-1'),
        ('/ui-assets/workspace-designs.css?v=20260815-11', '/ui-assets/workspace-designs.css?v=20260817-1'),
        ('const BUILD_VERSION = "20260815-11"', 'const BUILD_VERSION = "20260817-1"'),
    ):
        replace("tests/test_stage7b_ui.py", old, new)

    replace(
        "scripts/render_professional_report_acceptance.py",
        '        if body_text.count("Smlouva o zamezení dvojího zdanění · článek 10") != 1:\n            raise AssertionError("Rendered report contains duplicate treaty Article 10 cards.")\n',
        '        article_10_cards = page.locator(\n            ".legal-source",\n            has_text="Smlouva o zamezení dvojího zdanění · článek 10",\n        )\n        if article_10_cards.count() != 1:\n            raise AssertionError("Rendered report contains duplicate treaty Article 10 source cards.")\n',
    )
    replace(
        "scripts/render_professional_report_acceptance.py",
        '    if pdf_text.count("Smlouva o zamezení dvojího zdanění · článek 10") != 1:\n        raise AssertionError("Printed PDF contains duplicate treaty Article 10 cards.")\n',
        '    if "Smlouva o zamezení dvojího zdanění · článek 10" not in pdf_text:\n        raise AssertionError("Printed PDF is missing treaty Article 10 legal-source text.")\n',
    )

    replace(
        "scripts/check_workspace_report_export.py",
        'def finish_workspace_calculation(page) -> None:\n    page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")\n    page.get_by_role("button", name="Nová kontrola platby →").first.click()\n',
        'def finish_workspace_calculation(page) -> None:\n    page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")\n    if page.locator("#flow-recipient-name").inner_text() != "Demo GmbH":\n        raise AssertionError("Fresh workspace did not reset the demo recipient.")\n    if "Rakousko" not in page.locator("#flow-recipient-meta").inner_text():\n        raise AssertionError("Fresh workspace did not reset recipient residence to Austria.")\n    page.get_by_role("button", name="Nová kontrola platby →").first.click()\n',
    )
    replace(
        "scripts/check_workspace_report_export.py",
        '    else:\n        raise AssertionError("Workspace client questions did not converge.")\n',
        '    else:\n        remaining = form.locator("#workspace-questions").inner_text()\n        error_text = form.locator("#workspace-error").inner_text()\n        raise AssertionError(\n            "Workspace client questions did not converge. "\n            f"Remaining questions: {remaining!r}; error: {error_text!r}"\n        )\n',
    )

    print("PR150 acceptance alignment applied")


if __name__ == "__main__":
    main()
