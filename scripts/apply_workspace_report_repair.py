from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Expected marker missing: {label}")
    return text.replace(old, new, 1)


def patch_workspace_html() -> None:
    path = ROOT / "app" / "web" / "workspace.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace("workspace.css?v=20260815-11", "workspace.css?v=20260817-1")
    text = text.replace("workspace-designs.css?v=20260815-11", "workspace-designs.css?v=20260817-1")
    text = text.replace("workspace.js?v=20260815-11", "workspace.js?v=20260817-1")
    text = text.replace("workspace-report-export.js?v=20260816-1", "workspace-report-export.js?v=20260817-1")
    text = text.replace(
        '<div class="card-head"><h2>Odborné ověření</h2><span id="workspace-action-count">0</span></div>',
        '<div class="card-head"><h2>Podmínky a další kroky</h2><span id="workspace-action-count">0</span></div>',
    )
    text = text.replace(
        '<label class="form-field form-field-wide"><span><b>01</b> Název nebo jméno *</span>',
        '<label class="form-field form-field-wide"><span>Název nebo jméno *</span>',
    )
    text = text.replace(
        '<label class="form-field"><span><b>02</b> Stát daňové rezidence *</span>',
        '<label class="form-field"><span>Stát daňové rezidence *</span>',
    )
    text = text.replace(
        '<label class="form-field"><span><b>03</b> Typ příjemce *</span>',
        '<label class="form-field"><span>Typ příjemce *</span>',
    )
    path.write_text(text, encoding="utf-8")


def patch_workspace_css() -> None:
    path = ROOT / "app" / "web" / "workspace.css"
    text = path.read_text(encoding="utf-8")
    marker = ".form-field input:focus,.form-field select:focus{outline:3px solid #dfe6ff;border-color:var(--blue)}"
    replacement = marker + ".mini-form input,.mini-form select{pointer-events:auto!important;user-select:text;position:relative;z-index:2}.mini-form{position:relative;z-index:2}"
    text = replace_once(text, marker, replacement, "recipient form interaction CSS")
    path.write_text(text, encoding="utf-8")


def patch_workspace_js() -> None:
    path = ROOT / "app" / "web" / "workspace.js"
    text = path.read_text(encoding="utf-8")
    old = '  const BUILD_VERSION = "20260815-11";'
    text = replace_once(text, old, '  const BUILD_VERSION = "20260817-1";', "workspace build version")

    old_maps = '  const countryNames = { AT: "Rakousko", CH: "Švýcarsko", DE: "Německo", SG: "Singapur", TW: "Tchaj-wan" };\n  const countryGenitives = { AT: "Rakouska", CH: "Švýcarska", DE: "Německa", SG: "Singapuru", TW: "Tchaj-wanu" };'
    new_maps = '''  const regionNames = new Intl.DisplayNames(["cs-CZ"], { type: "region" });
  const knownCountryGenitives = { AT: "Rakouska", CH: "Švýcarska", DE: "Německa", SG: "Singapuru", TW: "Tchaj-wanu" };
  function countryName(code) {
    try { return regionNames.of(String(code || "").toUpperCase()) || String(code || ""); }
    catch (_problem) { return String(code || ""); }
  }
  function countryGenitive(code) {
    return knownCountryGenitives[String(code || "").toUpperCase()] || countryName(code);
  }
  async function loadJurisdictionCatalog() {
    const selects = [recipientForm?.elements.recipient_country, recipientEditForm?.elements.recipient_country].filter(Boolean);
    selects.forEach((select) => { select.disabled = true; });
    try {
      const response = await fetch("/jurisdictions", { cache: "no-store" });
      const body = await response.json();
      if (!response.ok || !Array.isArray(body.jurisdictions) || body.jurisdictions.length !== 101) {
        throw new Error("Incomplete jurisdiction catalog");
      }
      const jurisdictions = [...body.jurisdictions].sort((a, b) =>
        countryName(a.iso2).localeCompare(countryName(b.iso2), "cs")
      );
      selects.forEach((select) => {
        const current = select.value;
        const placeholder = select.closest("#new-recipient-form") ? "Vyber stát" : null;
        select.replaceChildren();
        if (placeholder) {
          const option = document.createElement("option"); option.value = ""; option.textContent = placeholder; select.append(option);
        }
        jurisdictions.forEach((item) => {
          const option = document.createElement("option");
          option.value = item.iso2;
          option.textContent = countryName(item.iso2);
          select.append(option);
        });
        if ([...select.options].some((option) => option.value === current)) select.value = current;
      });
    } catch (_problem) {
      // Keep the server-rendered fallback rather than blocking the workspace.
    } finally {
      selects.forEach((select) => { select.disabled = false; });
    }
  }'''
    text = replace_once(text, old_maps, new_maps, "dynamic country catalog")

    text = text.replace("const country = countryNames[recipient.country];", "const country = countryName(recipient.country);")
    text = text.replace("countryGenitives[recipient.country]", "countryGenitive(recipient.country)")

    old_create = '''  document.querySelectorAll("[data-create-recipient]").forEach((button) => button.addEventListener("click", () => {
    showStep(2);
    recipientForm.hidden = false;
    recipientForm.querySelector("input").focus();
  }));'''
    new_create = '''  document.querySelectorAll("[data-create-recipient]").forEach((button) => button.addEventListener("click", () => {
    showStep(2);
    recipientForm.hidden = false;
    recipientForm.querySelectorAll("input,select").forEach((field) => { field.disabled = false; field.readOnly = false; });
    recipientForm.querySelector("input").focus();
  }));'''
    text = replace_once(text, old_create, new_create, "create-recipient interaction")

    old_toggle = '''  document.querySelector("[data-show-recipient-form]").addEventListener("click", () => {
    recipientForm.hidden = !recipientForm.hidden;
    if (!recipientForm.hidden) recipientForm.querySelector("input").focus();
  });'''
    new_toggle = '''  document.querySelector("[data-show-recipient-form]").addEventListener("click", () => {
    recipientForm.hidden = !recipientForm.hidden;
    if (!recipientForm.hidden) {
      recipientForm.querySelectorAll("input,select").forEach((field) => { field.disabled = false; field.readOnly = false; });
      recipientForm.querySelector("input").focus();
    }
  });'''
    text = replace_once(text, old_toggle, new_toggle, "recipient-form toggle")

    startup_marker = "  renderPayers();\n  renderRecipient();"
    text = replace_once(text, startup_marker, "  renderPayers();\n  renderRecipient();\n  loadJurisdictionCatalog();", "jurisdiction startup")
    path.write_text(text, encoding="utf-8")


def patch_output_history() -> None:
    path = ROOT / "app" / "web" / "workspace-report-export.js"
    text = path.read_text(encoding="utf-8")
    text = text.replace('"ODBORNÉ OVĚŘENÍ"', '"VYŽADUJE DOPLNĚNÍ"')
    text = text.replace('"výsledků k odbornému ověření"', '"výsledků s otevřenými podmínkami"')
    text = text.replace("workspace-output-history.css?v=20260816-2", "workspace-output-history.css?v=20260817-1")
    path.write_text(text, encoding="utf-8")


def patch_reporting() -> None:
    path = ROOT / "taxtreat" / "services" / "reporting.py"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'DISCLAIMER = \(.*?\n\)\n',
        'DISCLAIMER = (\n    "Výstup vychází ze zadaných údajů a z právních pravidel evidovaných "\n    "v TaxTreat. Slouží jako pracovní podklad a nepředstavuje právní ani "\n    "daňové poradenství nebo závazné stanovisko správce daně."\n)\n',
        text,
        count=1,
        flags=re.S,
    )
    text = text.replace(
        '"Před použitím výsledku je vyžadováno doplnění údajů nebo "\n            "odborné ověření označených podmínek."',
        '"Před použitím výsledku je potřeba doplnit otevřené skutkové "\n            "údaje nebo uzavřít označené podmínky."',
    )
    text = text.replace(
        '"Výsledek vyžaduje doplnění nebo odborné ověření",',
        '"Výsledek vyžaduje doplnění údajů",',
    )

    new_renderer = r'''def _report_date(value: Any) -> str:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return f"{parsed.day}. {parsed.month}. {parsed.year}"
    except ValueError:
        return text or "—"


def _income_type_label(value: Any) -> str:
    return {
        "dividend": "Dividendy",
        "interest": "Úroky",
        "royalty": "Licenční poplatky",
    }.get(str(value), str(value or "—"))


def render_report_html(report: Mapping[str, Any]) -> str:
    scope = report["scope"]
    result = report["result"]
    calculation = result.get("withholding_tax_calculation")
    schedule = result.get("withholding_compliance_schedule") or {}
    conclusion, conclusion_detail = _result_copy(result)
    treatment = result.get("tax_treatment")
    non_taxing = treatment in {"exclusive_foreign_taxation", "domestic_exemption"}

    if calculation and calculation.get("status") == "CALCULATED":
        tax_label = "Česká daň k odvodu" if non_taxing else "Srážková daň"
        rate_value = "Neuplatňuje se" if non_taxing else f"{escape(str(result.get('rate')))} %"
        exchange = calculation.get("exchange_rate")
        exchange_row = ""
        if exchange:
            source_url = escape(str(exchange.get("source_url") or ""), quote=True)
            exchange_row = (
                '<div class="metric"><span>Přepočet ČNB</span><strong>'
                f"1 {escape(str(exchange['currency']))} = {escape(str(exchange['czk_per_unit']))} CZK"
                f'</strong><small>{_report_date(exchange.get("effective_date"))} · '
                f'<a href="{source_url}">kurzovní lístek ČNB</a></small></div>'
            )
        calculation_html = f"""
        <div class="metric-grid">
          <div class="metric"><span>Hrubá částka</span><strong>{escape(str(calculation['gross_amount']))} {escape(str(calculation['transaction_currency']))}</strong></div>
          <div class="metric"><span>Daňový základ</span><strong>{escape(str(calculation['gross_amount_czk']))} Kč</strong></div>
          <div class="metric primary-metric"><span>{tax_label}</span><strong>{escape(str(calculation['withholding_tax_czk']))} Kč</strong></div>
          <div class="metric"><span>Použitá sazba</span><strong>{rate_value}</strong></div>
          {exchange_row}
        </div>"""
    else:
        calculation_html = '<p class="note">Částkový výpočet nebyl uzavřen.</p>'

    source_items: list[str] = []
    for source in report.get("official_sources", []):
        url = escape(str(source.get("source_url") or ""), quote=True)
        excerpt = escape(str(source.get("excerpt") or ""))
        excerpt_html = (
            f"<details><summary>Zobrazit přesné znění ustanovení</summary><blockquote>{excerpt}</blockquote></details>"
            if excerpt else ""
        )
        source_items.append(
            '<article class="legal-source"><div><h3>'
            f'{_source_title(source)}</h3><a href="{url}">Otevřít zdroj ↗</a></div>{excerpt_html}</article>'
        )
    if not source_items:
        source_items.append('<p class="note">Pro tento výsledek nebyl vybrán konkrétní právní zdroj.</p>')

    missing = report.get("missing_facts", [])
    missing_items = "".join(
        f"<li>{escape(_FACT_LABELS.get(str(item), str(item).replace('_', ' ')))}</li>" for item in missing
    ) or "<li>Žádné otevřené skutkové údaje.</li>"
    documents = "".join(f"<li>{escape(str(item))}</li>" for item in report.get("required_documentation", []))
    amount = scope.get("transaction_amount") or {}
    amount_copy = f"{escape(str(amount.get('amount')))} {escape(str(amount.get('currency')))}" if amount else "Neuvedena"

    deadline_rows = []
    labels = {
        "reference_date": "Rozhodné datum",
        "remittance_deadline": "Odvod srážkové daně",
        "notification_deadline": "Oznámení příjmu do zahraničí",
    }
    for key, label in labels.items():
        value = schedule.get(key)
        if value:
            deadline_rows.append(f"<div><span>{label}</span><strong>{_report_date(value)}</strong></div>")
    compliance_html = "".join(deadline_rows) or '<p class="note">Navazující lhůty nejsou pro tento výsledek k dispozici.</p>'

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>TaxTreat · Analýza srážkové daně</title>
  <style>
    :root {{ --navy:#172b4d; --blue:#3157d5; --ink:#172033; --muted:#657085; --line:#dfe4ec; --soft:#f5f7fb; --paper:#ffffff; --green:#176c4f; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:#edf1f6; font:14px/1.55 Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }}
    .report {{ width:min(1040px,calc(100% - 36px)); margin:28px auto; background:var(--paper); box-shadow:0 16px 50px #172b4d14; }}
    header {{ display:flex; justify-content:space-between; gap:28px; padding:28px 38px; color:#fff; background:var(--navy); }}
    .brand {{ font-size:20px; font-weight:800; letter-spacing:-.02em; }}
    .brand span {{ display:inline-grid; place-items:center; width:34px; height:34px; margin-right:10px; border-radius:8px; color:#fff; background:var(--blue); font-size:12px; vertical-align:middle; }}
    header p {{ margin:5px 0 0; color:#cbd6e7; }} header .cutoff {{ align-self:center; text-align:right; font-size:12px; }}
    main {{ padding:34px 38px 42px; }}
    h1 {{ margin:0; font-size:30px; letter-spacing:-.035em; }} h2 {{ margin:0 0 16px; color:var(--navy); font-size:20px; }} h3 {{ margin:0 0 5px; font-size:14px; }}
    .transaction {{ margin-bottom:26px; padding:24px; border:1px solid #cad5e7; border-top:5px solid var(--blue); background:#fbfcff; }}
    .transaction .eyebrow,.verdict .eyebrow {{ color:var(--blue); font-size:11px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }}
    .transaction h1 {{ margin:6px 0 20px; }}
    .transaction-grid {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); border:1px solid var(--line); background:#fff; }}
    .transaction-grid div {{ min-height:72px; padding:13px 14px; border-right:1px solid var(--line); }} .transaction-grid div:last-child {{ border-right:0; }}
    .transaction-grid span,.metric span,.deadline-grid span {{ display:block; color:var(--muted); font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
    .transaction-grid strong {{ display:block; margin-top:6px; font-size:14px; }}
    .verdict {{ margin-bottom:30px; padding:25px 28px; border-left:5px solid var(--blue); background:#eef3ff; }}
    .verdict h2 {{ margin:7px 0 7px; font-size:25px; }} .verdict p {{ max-width:780px; color:#46536a; }}
    section {{ padding:26px 0; border-top:1px solid var(--line); }}
    .metric-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); border-top:1px solid var(--line); border-left:1px solid var(--line); }}
    .metric {{ min-height:88px; padding:16px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); }} .metric strong {{ display:block; margin-top:7px; font-size:19px; }} .metric small {{ display:block; margin-top:4px; color:var(--muted); }}
    .primary-metric {{ background:#f0f4ff; }} .primary-metric strong {{ color:var(--blue); font-size:24px; }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:34px; }} ul {{ margin:0; padding-left:18px; }} li {{ margin:7px 0; }}
    .deadline-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }} .deadline-grid div {{ padding:14px; border:1px solid var(--line); background:var(--soft); }} .deadline-grid strong {{ display:block; margin-top:5px; }}
    .legal-source {{ padding:16px 0; border-top:1px solid var(--line); }} .legal-source:first-of-type {{ border-top:0; }} .legal-source a {{ color:var(--blue); font-weight:700; text-decoration:none; }}
    details {{ margin-top:10px; }} summary {{ cursor:pointer; color:var(--blue); font-weight:700; }} blockquote {{ max-height:260px; overflow:auto; margin:12px 0 0; padding:15px 17px; white-space:pre-line; color:#334158; background:var(--soft); border-left:3px solid #b9c7e7; font-size:12px; }}
    .note {{ color:var(--muted); }} .risk {{ margin-top:12px; color:#4c596e; }}
    footer {{ padding:20px 38px 26px; border-top:1px solid var(--line); color:var(--muted); background:#fafbfc; font-size:10px; }}
    @media(max-width:760px) {{ .report{{width:100%;margin:0}} header{{display:block}} header .cutoff{{margin-top:16px;text-align:left}} main{{padding:24px 20px}} .transaction-grid{{grid-template-columns:1fr 1fr}} .transaction-grid div{{border-bottom:1px solid var(--line)}} .metric-grid,.two-col,.deadline-grid{{grid-template-columns:1fr}} }}
    @media print {{ @page{{size:A4;margin:13mm}} body{{background:#fff}} .report{{width:auto;margin:0;box-shadow:none}} header{{print-color-adjust:exact;-webkit-print-color-adjust:exact}} section,.verdict,.transaction,.legal-source{{break-inside:avoid}} a{{color:inherit;text-decoration:none}} details{{display:block}} }}
  </style>
</head>
<body><article class="report">
  <header><div><div class="brand"><span>TT</span>TaxTreat</div><p>Withholding tax analysis</p></div><div class="cutoff">Právní stav k {_report_date(report.get('legal_data_cutoff'))}</div></header>
  <main>
    <section class="transaction"><div class="eyebrow">Analyzovaná transakce</div><h1>Česká srážková daň</h1><div class="transaction-grid">
      <div><span>Zdroj příjmu</span><strong>{escape(str(scope.get('source_country') or '—'))}</strong></div>
      <div><span>Rezidence příjemce</span><strong>{escape(str(scope.get('recipient_country') or '—'))}</strong></div>
      <div><span>Druh příjmu</span><strong>{escape(_income_type_label(scope.get('income_type')))}</strong></div>
      <div><span>Datum transakce</span><strong>{_report_date(scope.get('transaction_date'))}</strong></div>
      <div><span>Částka</span><strong>{amount_copy}</strong></div>
    </div></section>
    <section class="verdict"><div class="eyebrow">Výsledek</div><h2>{escape(conclusion)}</h2><p>{escape(conclusion_detail)}</p></section>
    <section><h2>Výpočet</h2>{calculation_html}<p class="risk">{escape(str(report['risk_assessment']))}</p></section>
    <section><h2>Podmínky a podklady</h2><div class="two-col"><div><h3>Otevřené skutkové údaje</h3><ul>{missing_items}</ul></div><div><h3>Podklady k dokumentaci</h3><ul>{documents}</ul></div></div></section>
    <section><h2>Daňový kalendář</h2><div class="deadline-grid">{compliance_html}</div></section>
    <section><h2>Právní základ</h2>{''.join(source_items)}</section>
  </main>
  <footer>{escape(str(report['disclaimer']))}</footer>
</article></body></html>"""
'''
    text, count = re.subn(
        r'def render_report_html\(report: Mapping\[str, Any\]\) -> str:.*\Z',
        new_renderer,
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("Could not replace report renderer")
    path.write_text(text, encoding="utf-8")


def patch_browser_acceptance() -> None:
    path = ROOT / "scripts" / "check_workspace_report_export.py"
    text = path.read_text(encoding="utf-8")
    marker = "\ndef finish_workspace_calculation(page) -> None:\n"
    helper = '''\ndef verify_recipient_catalog_and_entry(page) -> None:\n    page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")\n    page.get_by_role("button", name="Příjemci", exact=True).click()\n    page.get_by_role("button", name="Přidat příjemce", exact=True).click()\n    form = page.locator("#new-recipient-form")\n    form.wait_for(state="visible")\n    country = form.locator('select[name="recipient_country"]')\n    page.wait_for_function(\n        "() => document.querySelector('#new-recipient-form select[name=recipient_country]').options.length === 102",\n        timeout=5000,\n    )\n    if country.locator("option").count() != 102:\n        raise AssertionError("Recipient form does not expose all 101 jurisdictions.")\n    name = form.locator('input[name="recipient_name"]')\n    name.fill("Test Korea Co.")\n    if name.input_value() != "Test Korea Co.":\n        raise AssertionError("Recipient name field is not writable.")\n    country.select_option("KR")\n    form.get_by_role("button", name="Použít příjemce v této kontrole →").click()\n    if page.locator("#flow-recipient-name").inner_text() != "Test Korea Co.":\n        raise AssertionError("New recipient was not applied to the workspace.")\n    if "undefined" in page.locator("#flow-recipient-meta").inner_text().lower():\n        raise AssertionError("Dynamic jurisdiction name was not rendered.")\n\n'''
    text = replace_once(text, marker, helper + marker, "recipient browser helper")
    text = replace_once(
        text,
        "            finish_workspace_calculation(page)\n",
        "            verify_recipient_catalog_and_entry(page)\n            finish_workspace_calculation(page)\n",
        "recipient browser invocation",
    )
    text = text.replace('if review_status not in {"DOKONČENO", "ODBORNÉ OVĚŘENÍ"}:', 'if review_status not in {"DOKONČENO", "VYŽADUJE DOPLNĚNÍ"}:')
    text = text.replace('expected_attention = "1" if review_status == "ODBORNÉ OVĚŘENÍ" else "0"', 'expected_attention = "1" if review_status == "VYŽADUJE DOPLNĚNÍ" else "0"')
    old_report_assert = '            report_page.get_by_text("Česká srážková daň", exact=True).wait_for()\n'
    new_report_assert = '''            report_page.get_by_text("Česká srážková daň", exact=True).wait_for()\n            report_page.get_by_text("Analyzovaná transakce", exact=True).wait_for()\n            report_page.get_by_text("Právní základ", exact=True).wait_for()\n            if report_page.locator(".section-no,.source-number").count() != 0:\n                raise AssertionError("Report still exposes internal section/source numbering.")\n            if "TAXTREAT-" in report_page.locator("body").inner_text():\n                raise AssertionError("Report still exposes an internal report identifier.")\n            if "Odborné ověření" in report_page.locator("body").inner_text():\n                raise AssertionError("Report still exposes obsolete human-review wording.")\n'''
    text = replace_once(text, old_report_assert, new_report_assert, "professional report assertions")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_workspace_html()
    patch_workspace_css()
    patch_workspace_js()
    patch_output_history()
    patch_reporting()
    patch_browser_acceptance()
    print("Workspace/report repair applied.")


if __name__ == "__main__":
    main()
