from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Missing marker {label} in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    path = ROOT / "taxtreat" / "services" / "reporting.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        'risk = "Výsledek byl určen z uvolněného katalogu právních pravidel."',
        'risk = "Výsledek vychází ze zadaných údajů a z právních pravidel uvedených v tomto výstupu."',
    )
    text = text.replace(
        '<header><div><div class="brand"><span>TT</span>TaxTreat</div><p>Withholding tax analysis</p></div><div class="cutoff">',
        '<header><div><div class="brand"><span>TT</span>TaxTreat</div><p>Analýza české srážkové daně</p></div><div class="cutoff">',
    )
    text = text.replace(
        '@media print {{ @page{{size:A4;margin:13mm}} body{{background:#fff}} .report{{width:auto;margin:0;box-shadow:none}} header{{print-color-adjust:exact;-webkit-print-color-adjust:exact}} section,.verdict,.transaction,.legal-source{{break-inside:avoid}} a{{color:inherit;text-decoration:none}} details{{display:block}} }}',
        '@media print {{ @page{{size:A4;margin:13mm}} body{{background:#fff}} .report{{width:auto;margin:0;box-shadow:none}} header{{print-color-adjust:exact;-webkit-print-color-adjust:exact}} section,.verdict,.transaction{{break-inside:avoid}} a{{color:inherit;text-decoration:none}} details{{display:block}} blockquote{{max-height:none;overflow:visible;break-inside:auto}} .legal-source{{break-inside:auto}} }}',
    )

    marker = '''    source_items: list[str] = []\n    for source in report.get("official_sources", []):'''
    insert = '''    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")\n    selected_source = next(\n        (source for source in report.get("official_sources", []) if source.get("rule_id") == selected_rule_id),\n        None,\n    )\n    if selected_source and selected_source.get("legal_layer") in {"treaty", "protocol", "mli"}:\n        why_result = (\n            "Použitá sazba vychází z příslušné smlouvy o zamezení dvojího zdanění. "\n            f"Rozhodující právní základ je {_source_title(selected_source)}; níže je uveden oficiální zdroj i přesné znění ustanovení."\n        )\n    elif selected_source:\n        why_result = (\n            f"Výsledek vychází z {_source_title(selected_source)}. "\n            "Níže je uveden oficiální zdroj a právní podklad použitý při výpočtu."\n        )\n    else:\n        why_result = "Výsledek vychází ze zadaných údajů a z právních podkladů uvedených níže."\n\n    source_items: list[str] = []\n    for source in report.get("official_sources", []):'''
    if marker not in text:
        raise RuntimeError("Legal source marker missing")
    text = text.replace(marker, insert, 1)
    text = text.replace(
        '<section><h2>Právní základ</h2>{\'\'.join(source_items)}</section>',
        '<section><h2>Proč tato sazba</h2><p class="risk">{why_result}</p></section>\n    <section><h2>Právní základ</h2>{\'\'.join(source_items)}</section>',
    )
    path.write_text(text, encoding="utf-8")

    acceptance = ROOT / "scripts" / "check_workspace_report_export.py"
    browser = acceptance.read_text(encoding="utf-8")
    anchor = '            report_page.get_by_text("Právní základ", exact=True).wait_for()\n'
    addition = anchor + '            report_page.get_by_text("Proč tato sazba", exact=True).wait_for()\n'
    if anchor not in browser:
        raise RuntimeError("Report browser heading marker missing")
    browser = browser.replace(anchor, addition, 1)
    browser = browser.replace(
        '            if "Odborné ověření" in report_page.locator("body").inner_text():\n                raise AssertionError("Report still exposes obsolete human-review wording.")\n',
        '            report_body = report_page.locator("body").inner_text()\n            if "Odborné ověření" in report_body or "uvolněného katalogu" in report_body or "Withholding tax analysis" in report_body:\n                raise AssertionError("Report still exposes obsolete or internal-facing wording.")\n',
    )
    acceptance.write_text(browser, encoding="utf-8")

    report_acceptance = ROOT / "scripts" / "render_professional_report_acceptance.py"
    ra = report_acceptance.read_text(encoding="utf-8")
    marker2 = '        "Právní základ",\n'
    if marker2 in ra and '"Proč tato sazba",' not in ra:
        ra = ra.replace(marker2, marker2 + '        "Proč tato sazba",\n', 1)
    report_acceptance.write_text(ra, encoding="utf-8")
    print("Professional report polished.")


if __name__ == "__main__":
    main()
