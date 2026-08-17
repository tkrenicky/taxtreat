from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Static unit contract.
p = ROOT / "tests/test_workspace_report_export.py"
t = p.read_text(encoding="utf-8")
t = t.replace('    assert "Tisk / uložit PDF" in asset.text\n', '')
t = t.replace('def test_workspace_loads_professional_report_export_asset():', 'def test_workspace_loads_pdf_report_export_asset():')
t = t.replace('def test_workspace_output_history_is_in_memory_and_reopenable():', 'def test_workspace_output_history_is_in_memory_and_printable():')
p.write_text(t, encoding="utf-8")

# Browser acceptance: one export action only, and new client-report structure.
p = ROOT / "scripts/check_workspace_report_export.py"
t = p.read_text(encoding="utf-8")
start = t.index('            open_button = page.locator(\'[data-report-action="open"]\')')
end = t.index('            page.get_by_role("button", name="Výstupy", exact=True).click()', start)
replacement = '''            print_button = page.locator('[data-report-action="print"]')\n            if print_button.count() != 1:\n                raise AssertionError("Workspace PDF report action is missing.")\n            if page.locator('[data-report-action="open"]').count() != 0:\n                raise AssertionError("Obsolete open-report action is still exposed.")\n\n            requests_before_direct_export = len(report_requests)\n            with page.expect_popup() as print_popup_info:\n                print_button.click()\n            print_page = print_popup_info.value\n            print_page.wait_for_load_state("domcontentloaded")\n            print_page.get_by_text("Posouzení srážkové daně", exact=True).wait_for()\n            print_page.get_by_text("Odůvodnění výsledku", exact=True).wait_for()\n            print_page.get_by_text("Právní základ", exact=True).wait_for()\n            report_body = print_page.locator("body").inner_text()\n            if "TAXTREAT-" in report_body:\n                raise AssertionError("PDF report still exposes an internal report identifier.")\n            if "Otevřít profesionální report" in report_body or "Withholding tax analysis" in report_body:\n                raise AssertionError("PDF report still exposes obsolete/internal-facing wording.")\n            if print_page.locator(".legal-source").count() < 1:\n                raise AssertionError("PDF report contains no legal sources.")\n            print_page.wait_for_function(\n                "() => window.__taxtreatPrintCalled === true", timeout=5000\n            )\n            print_page.close()\n\n            if len(report_requests) < requests_before_direct_export + 1:\n                raise AssertionError("PDF export did not request /analysis/report.")\n\n'''
t = t[:start] + replacement + t[end:]
t = t.replace('stored_page.get_by_text("Česká srážková daň", exact=True).wait_for()', 'stored_page.get_by_text("Posouzení srážkové daně", exact=True).wait_for()')
p.write_text(t, encoding="utf-8")

# HTML→PDF acceptance should validate the new headline.
p = ROOT / "scripts/render_professional_report_acceptance.py"
t = p.read_text(encoding="utf-8")
t = t.replace('if "Česká srážková daň" not in body_text:', 'if "Posouzení srážkové daně" not in body_text:')
t = t.replace('raise AssertionError("Rendered report is missing its main heading.")', 'raise AssertionError("Rendered report is missing its main heading.")')
p.write_text(t, encoding="utf-8")

print("PDF-only acceptance aligned")
