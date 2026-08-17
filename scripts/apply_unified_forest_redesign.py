from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing marker: {label}")
    return text.replace(old, new, 1)


def patch_html() -> None:
    p = ROOT / "app/web/workspace.html"
    t = p.read_text(encoding="utf-8")
    t = t.replace('<body>', '<body data-design="atlas">', 1)
    t = t.replace('workspace.css?v=20260817-1', 'workspace.css?v=20260817-2')
    t = t.replace('workspace-designs.css?v=20260817-1', 'workspace-designs.css?v=20260817-2')
    t = t.replace('workspace.js?v=20260817-1', 'workspace.js?v=20260817-2')
    t = t.replace('workspace-report-export.js?v=20260817-1', 'workspace-report-export.js?v=20260817-2')
    p.write_text(t, encoding="utf-8")


def patch_design_css() -> None:
    p = ROOT / "app/web/workspace-designs.css"
    t = p.read_text(encoding="utf-8")
    t += r'''

/* 2026-08-17 — TaxTreat unified forest system. */
body[data-design="atlas"]{
  --forest:#173f39;--forest-2:#24584f;--forest-3:#dfe9e4;--lime:#b8d8a8;
  --ink:#17302b;--muted:#708078;--line:#e2e5df;--surface:#fff;--surface-soft:#f5f3ed;
  --blue:var(--forest-2);--blue-soft:#e7efeb;
  margin:0;color:var(--ink);background:#f2efe8!important;background-image:none!important;
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif!important;
}
body[data-design="atlas"] .app-header{
  position:fixed;z-index:40;inset:0 auto 0 0;width:248px;height:100vh!important;padding:28px 18px 22px!important;
  display:flex;flex-direction:column;align-items:stretch;gap:22px;border:0!important;border-radius:0!important;
  background:var(--forest)!important;box-shadow:none!important;
}
body[data-design="atlas"] .logo{display:flex;align-items:center;padding:0 10px;color:#fff!important;font:800 21px/1 Inter,ui-sans-serif,sans-serif!important;letter-spacing:-.03em}
body[data-design="atlas"] .logo span{width:36px;height:36px;border-radius:10px!important;color:var(--forest)!important;background:#d7e8cf!important;font:800 11px/36px Inter,sans-serif;text-align:center}
body[data-design="atlas"] .app-header nav{display:flex;flex-direction:column;align-items:stretch;gap:5px;width:100%}
body[data-design="atlas"] .app-header nav button{width:100%;padding:12px 14px;border-radius:10px!important;color:#c7d8d2!important;background:transparent!important;font:650 13px/1.2 Inter,sans-serif!important;text-align:left;letter-spacing:0!important}
body[data-design="atlas"] .app-header nav button:hover{color:#fff!important;background:#ffffff0c!important}
body[data-design="atlas"] .app-header nav button.active{color:#173f39!important;background:#d7e8cf!important}
body[data-design="atlas"] .payer-context{order:8;margin-top:auto;padding:11px 12px;border:1px solid #ffffff1f!important;border-radius:11px!important;background:#ffffff0b!important}
body[data-design="atlas"] .payer-context span{color:#9fb7af!important;font-size:10px!important;letter-spacing:.08em;text-transform:uppercase}
body[data-design="atlas"] .payer-context select{width:100%;padding:4px 0 0;color:#fff!important;background:transparent!important;font-weight:650}
body[data-design="atlas"] .account{order:9;padding:10px 8px;color:#b9ccc5!important;border-top:1px solid #ffffff18}
body[data-design="atlas"] .account b{color:var(--forest)!important;background:#d7e8cf!important}
body[data-design="atlas"] .demo-notice{margin:0 0 0 248px;padding:10px 34px;border:0!important;border-bottom:1px solid #e0e4dd!important;border-radius:0!important;color:#65766f!important;background:#f7f5ef!important;font:500 12px/1.4 Inter,sans-serif!important}
body[data-design="atlas"] .demo-notice strong{color:#365a51}
body[data-design="atlas"] main{max-width:none!important;margin-left:248px;padding:34px 42px 70px!important}
body[data-design="atlas"] .view{max-width:1420px;margin:0 auto}
body[data-design="atlas"] .page-title{margin-bottom:26px}
body[data-design="atlas"] .page-title p{margin-bottom:8px;color:#6b847b!important;font:750 10px/1 Inter,sans-serif!important;letter-spacing:.14em!important}
body[data-design="atlas"] .page-title h1{color:#183f38;font:760 34px/1.05 Inter,sans-serif!important;letter-spacing:-.04em!important;text-transform:none!important}
body[data-design="atlas"] .page-title span{color:#75847e}
body[data-design="atlas"] .card,body[data-design="atlas"] .metrics article{border:1px solid #e2e5df!important;border-radius:14px!important;background:#fff!important;box-shadow:0 5px 18px #213e3310!important}
body[data-design="atlas"] .dashboard-summary{gap:18px}
body[data-design="atlas"] .onboarding{border:1px solid #d8e1da!important;background:linear-gradient(120deg,#fff,#f0f5f1)!important;box-shadow:0 5px 18px #213e3310!important}
body[data-design="atlas"] .onboarding .icon{color:#fff;background:var(--forest-2)!important}
body[data-design="atlas"] .metrics article strong{color:#173f39;font-size:29px}
body[data-design="atlas"] .primary{border:0!important;border-radius:9px!important;color:#fff!important;background:var(--forest-2)!important;box-shadow:none!important}
body[data-design="atlas"] .primary:hover{background:#1e4c44!important}
body[data-design="atlas"] .secondary,body[data-design="atlas"] .new-recipient-toggle{border:1px solid #ced8d2!important;border-radius:9px!important;color:#244f47!important;background:#fff!important;box-shadow:none!important}
body[data-design="atlas"] input,body[data-design="atlas"] select,body[data-design="atlas"] textarea{border:1px solid #d8ddd8!important;border-radius:9px!important;color:#203c35!important;background:#fff!important;box-shadow:none!important}
body[data-design="atlas"] input:focus,body[data-design="atlas"] select:focus,body[data-design="atlas"] textarea:focus{outline:3px solid #dbe9e3!important;border-color:#5a8779!important}
body[data-design="atlas"] .card-head h2,body[data-design="atlas"] .flow-step h2{color:#173f39}
body[data-design="atlas"] .card-head span,body[data-design="atlas"] .badge{color:#315e52!important;background:#e5efe9!important}
body[data-design="atlas"] .flow-progress button b{border-radius:9px!important;border-color:#cad7d1!important;color:#61766e!important;background:#fff!important}
body[data-design="atlas"] .flow-progress button.active b{color:#fff!important;background:var(--forest-2)!important}
body[data-design="atlas"] .flow-progress i{background:#dfe5e1!important}
body[data-design="atlas"] .question-card,body[data-design="atlas"] .fact-question,body[data-design="atlas"] .citation-card.context{border:1px solid #e0e4df!important;border-radius:12px!important;background:#fbfcfa!important}
body[data-design="atlas"] .attention{border-top:3px solid #d9b56b!important}
body[data-design="atlas"] .output-history-row,body[data-design="atlas"] .review-history-row{border-color:#e2e5df!important;background:#fff!important}
body[data-design="atlas"] dialog{border:0!important;border-radius:16px!important;box-shadow:0 24px 80px #173f3933!important}
body[data-design="atlas"] dialog::backdrop{background:#102e295e!important;backdrop-filter:blur(3px)}
@media(max-width:1020px){
 body[data-design="atlas"] .app-header{position:sticky;inset:auto;width:auto;height:auto!important;padding:14px 18px!important;flex-direction:row;align-items:center;border-radius:0!important}
 body[data-design="atlas"] .app-header nav{flex-direction:row;width:auto;overflow:auto}body[data-design="atlas"] .app-header nav button{width:auto;white-space:nowrap}
 body[data-design="atlas"] .payer-context{display:none}body[data-design="atlas"] .account{display:none}
 body[data-design="atlas"] .demo-notice{margin-left:0}body[data-design="atlas"] main{margin-left:0;padding:26px 18px 54px!important}
}
'''
    p.write_text(t, encoding="utf-8")


def patch_export_js() -> None:
    p = ROOT / "app/web/workspace-report-export.js"
    t = p.read_text(encoding="utf-8")
    t = t.replace('workspace-output-history.css?v=20260817-1', 'workspace-output-history.css?v=20260817-2')
    t = t.replace(
'''    actions.append(
      actionButton("Otevřít report", () => openStoredReport(record)),
      actionButton("Tisk / PDF", () => openStoredReport(record, true)),
    );''',
'''    actions.append(
      actionButton("Tisk / PDF", () => openStoredReport(record, true)),
    );''')
    t = t.replace(
'''    const action = actionButton(
      "Otevřít výstup",
      () => openStoredReport(record)
    );''',
'''    const action = actionButton(
      "Tisk / PDF",
      () => openStoredReport(record, true)
    );''')
    old = '''  openButton.removeAttribute("data-nav");
  openButton.type = "button";
  openButton.textContent = "Otevřít profesionální report";
  openButton.dataset.reportAction = "open";

  const printButton = document.createElement("button");
  printButton.type = "button";
  printButton.className = "secondary";
  printButton.textContent = "Tisk / uložit PDF";
  printButton.dataset.reportAction = "print";
  resultActions.insertBefore(printButton, openButton);'''
    new = '''  openButton.removeAttribute("data-nav");
  openButton.type = "button";
  openButton.textContent = "Tisk / PDF reportu";
  openButton.dataset.reportAction = "print";'''
    t = replace_once(t, old, new, "step 4 report actions")
    old2 = '''  openButton.addEventListener(
    "click",
    (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      exportReport(false, openButton);
    },
    true
  );

  printButton.addEventListener("click", () => {
    exportReport(true, printButton);
  });'''
    new2 = '''  openButton.addEventListener(
    "click",
    (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      exportReport(true, openButton);
    },
    true
  );'''
    t = replace_once(t, old2, new2, "print only handler")
    t = t.replace("Připravuji profesionální report…", "Připravuji PDF report…")
    p.write_text(t, encoding="utf-8")


def patch_reporting() -> None:
    p = ROOT / "taxtreat/services/reporting.py"
    t = p.read_text(encoding="utf-8")
    helper_marker = '''def _income_type_label(value: Any) -> str:
    return {
        "dividend": "Dividendy",
        "interest": "Úroky",
        "royalty": "Licenční poplatky",
    }.get(str(value), str(value or "—"))


'''
    helper_new = helper_marker + '''def _format_number(value: Any, *, maximum_decimals: int = 2) -> str:
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return escape(str(value))
    if number.is_integer():
        rendered = f"{int(number):,}"
    else:
        rendered = f"{number:,.{maximum_decimals}f}".rstrip("0").rstrip(".")
    return rendered.replace(",", " ")


def _format_rate(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return f"{_format_number(value)} %"


'''
    t = replace_once(t, helper_marker, helper_new, "number formatter")

    start = t.index('def render_report_html(report: Mapping[str, Any]) -> str:')
    prefix = t[:start]
    renderer = r'''def render_report_html(report: Mapping[str, Any]) -> str:
    scope = report["scope"]
    result = report["result"]
    calculation = result.get("withholding_tax_calculation")
    schedule = result.get("withholding_compliance_schedule") or {}
    conclusion, conclusion_detail = _result_copy(result)
    treatment = result.get("tax_treatment")
    non_taxing = treatment in {"exclusive_foreign_taxation", "domestic_exemption"}

    amount = scope.get("transaction_amount") or {}
    amount_copy = (
        f"{_format_number(amount.get('amount'))} {escape(str(amount.get('currency') or ''))}".strip()
        if amount else "Neuvedena"
    )

    if calculation and calculation.get("status") == "CALCULATED":
        tax_label = "Česká daň k odvodu" if non_taxing else "Srážková daň"
        rate_value = "Neuplatňuje se" if non_taxing else _format_rate(result.get("rate"))
        exchange = calculation.get("exchange_rate")
        exchange_row = ""
        if exchange:
            source_url = escape(str(exchange.get("source_url") or ""), quote=True)
            exchange_row = f'''<tr><th>Kurz ČNB</th><td>1 {escape(str(exchange.get('currency') or ''))} = {_format_number(exchange.get('czk_per_unit'), maximum_decimals=6)} Kč</td><td>{_report_date(exchange.get('effective_date'))} · <a href="{source_url}">zdroj ČNB ↗</a></td></tr>'''
        calculation_html = f'''
          <table class="calculation-table">
            <tbody>
              <tr><th>Hrubá částka</th><td>{_format_number(calculation.get('gross_amount'))} {escape(str(calculation.get('transaction_currency') or ''))}</td><td>Částka zadaná pro analyzovanou transakci</td></tr>
              <tr><th>Daňový základ</th><td>{_format_number(calculation.get('gross_amount_czk'))} Kč</td><td>Hodnota po přepočtu do CZK</td></tr>
              <tr class="emphasis"><th>{tax_label}</th><td>{_format_number(calculation.get('withholding_tax_czk'))} Kč</td><td>Sazba {rate_value}</td></tr>
              {exchange_row}
            </tbody>
          </table>'''
    else:
        calculation_html = '<p class="empty-note">Částkový výpočet nebyl uzavřen.</p>'

    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    selected_source = next((s for s in report.get("official_sources", []) if s.get("rule_id") == selected_rule_id), None)
    if selected_source and selected_source.get("legal_layer") in {"treaty", "protocol", "mli"}:
        why_result = f"Sazba vychází z {_source_title(selected_source)} a ze skutkových údajů potvrzených pro tuto transakci."
    elif selected_source:
        why_result = f"Výsledek vychází z {_source_title(selected_source)} a ze skutkových údajů potvrzených pro tuto transakci."
    else:
        why_result = "Výsledek vychází ze zadaných údajů a z právních podkladů uvedených v tomto reportu."

    source_items = []
    for source in report.get("official_sources", []):
        url = escape(str(source.get("source_url") or ""), quote=True)
        excerpt = escape(str(source.get("excerpt") or ""))
        excerpt_html = f"<blockquote>{excerpt}</blockquote>" if excerpt else ""
        source_items.append(f'''<article class="legal-source"><div class="source-head"><h3>{_source_title(source)}</h3><a href="{url}">Oficiální zdroj ↗</a></div>{excerpt_html}</article>''')
    if not source_items:
        source_items.append('<p class="empty-note">Pro tento výsledek nebyl vybrán konkrétní právní zdroj.</p>')

    missing = report.get("missing_facts", [])
    missing_items = "".join(f"<li>{escape(_FACT_LABELS.get(str(item), str(item).replace('_', ' ')))}</li>" for item in missing) or "<li>Žádné otevřené skutkové údaje.</li>"
    documents = "".join(f"<li>{escape(str(item))}</li>" for item in report.get("required_documentation", []))

    deadline_rows = []
    labels = {"reference_date":"Rozhodné datum","remittance_deadline":"Odvod srážkové daně","notification_deadline":"Oznámení příjmu do zahraničí"}
    for key, label in labels.items():
        if schedule.get(key):
            deadline_rows.append(f"<div><span>{label}</span><strong>{_report_date(schedule[key])}</strong></div>")
    compliance_html = "".join(deadline_rows) or '<p class="empty-note">Navazující lhůty nejsou pro tento výsledek k dispozici.</p>'

    return f'''<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><title>TaxTreat · Report srážkové daně</title>
<style>
:root{{--forest:#173f39;--forest2:#28584f;--sage:#dce9e2;--cream:#f2efe8;--ink:#19342e;--muted:#6f7c77;--line:#dde3df;--white:#fff}}
*{{box-sizing:border-box}} body{{margin:0;color:var(--ink);background:var(--cream);font:13px/1.55 Inter,Arial,sans-serif}}
.report{{width:min(920px,calc(100% - 32px));margin:24px auto;background:#fff;box-shadow:0 12px 40px #173f3915}}
.masthead{{display:flex;justify-content:space-between;align-items:center;padding:25px 34px;color:#fff;background:var(--forest)}}
.brand{{font-size:19px;font-weight:800;letter-spacing:-.03em}} .brand-mark{{display:inline-grid;place-items:center;width:32px;height:32px;margin-right:9px;border-radius:9px;color:var(--forest);background:#d8e8d1;font-size:10px}}
.masthead small{{display:block;margin-top:5px;color:#bcd0c9}} .cutoff{{text-align:right;color:#d2dfda;font-size:10px;text-transform:uppercase;letter-spacing:.07em}}
main{{padding:34px}} .hero{{display:grid;grid-template-columns:1.25fr .75fr;gap:24px;padding:0 0 28px;border-bottom:1px solid var(--line)}}
.eyebrow{{margin-bottom:8px;color:#688079;font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}} h1{{margin:0 0 10px;font-size:29px;line-height:1.08;letter-spacing:-.04em}} .hero p{{margin:0;color:var(--muted)}}
.result-card{{padding:20px;border-radius:12px;background:#edf4f0;border:1px solid #d8e5de}} .result-card span{{display:block;color:#60766e;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}} .result-card strong{{display:block;margin-top:7px;color:var(--forest);font-size:21px;line-height:1.2}}
.transaction-strip{{display:grid;grid-template-columns:repeat(5,1fr);margin:24px 0 4px;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.transaction-strip div{{padding:13px 12px;border-right:1px solid var(--line)}} .transaction-strip div:last-child{{border-right:0}} .transaction-strip span{{display:block;color:#81908a;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.06em}} .transaction-strip strong{{display:block;margin-top:5px;font-size:12px}}
section{{padding:27px 0;border-bottom:1px solid var(--line)}} section:last-child{{border-bottom:0}} h2{{margin:0 0 15px;color:var(--forest);font-size:18px;letter-spacing:-.02em}} h3{{margin:0;font-size:13px}}
.summary-box{{padding:17px 19px;border-left:4px solid var(--forest2);background:#f6f8f6;color:#39524b}} .summary-box p{{margin:0}}
.calculation-table{{width:100%;border-collapse:collapse;border:1px solid var(--line)}} .calculation-table th,.calculation-table td{{padding:13px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} .calculation-table th{{width:24%;color:#536a63;background:#f8f9f7;font-size:11px}} .calculation-table td:nth-child(2){{width:26%;font-weight:750;font-size:14px}} .calculation-table td:nth-child(3){{color:var(--muted);font-size:11px}} .calculation-table .emphasis td,.calculation-table .emphasis th{{background:#edf4f0}} .calculation-table .emphasis td:nth-child(2){{color:var(--forest);font-size:18px}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:28px}} ul{{margin:8px 0 0;padding-left:18px}} li{{margin:5px 0}}
.deadlines{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}} .deadlines div{{padding:14px;border:1px solid var(--line);border-radius:9px;background:#fafbf9}} .deadlines span{{display:block;color:#7b8984;font-size:9px;text-transform:uppercase;font-weight:800;letter-spacing:.05em}} .deadlines strong{{display:block;margin-top:6px}}
.legal-source{{padding:14px 0;border-top:1px solid var(--line)}} .legal-source:first-of-type{{border-top:0}} .source-head{{display:flex;justify-content:space-between;gap:20px}} .legal-source a{{color:var(--forest2);font-weight:700;text-decoration:none;font-size:11px}}
blockquote{{margin:12px 0 0;padding:14px 16px;border-left:3px solid #9ebcb1;background:#f7f9f7;color:#40534d;white-space:pre-line;font:11px/1.55 Georgia,serif}}
.empty-note{{color:var(--muted)}} footer{{padding:18px 34px 24px;color:#78847f;background:#fafaf8;border-top:1px solid var(--line);font-size:9px}}
@media(max-width:720px){{.report{{width:100%;margin:0}} main{{padding:22px}} .hero,.two-col{{grid-template-columns:1fr}} .transaction-strip{{grid-template-columns:1fr 1fr}} .deadlines{{grid-template-columns:1fr}}}}
@media print{{@page{{size:A4;margin:11mm}} body{{background:#fff}} .report{{width:auto;margin:0;box-shadow:none}} .masthead{{print-color-adjust:exact;-webkit-print-color-adjust:exact}} section,.hero,.result-card,.calculation-table{{break-inside:avoid}} .legal-source{{break-inside:auto}} blockquote{{break-inside:auto}} a{{color:inherit;text-decoration:none}}}}
</style></head><body><article class="report">
<header class="masthead"><div><div class="brand"><span class="brand-mark">TT</span>TaxTreat</div><small>Analýza české srážkové daně</small></div><div class="cutoff">Právní stav<br><strong>{_report_date(report.get('legal_data_cutoff'))}</strong></div></header>
<main>
<div class="hero"><div><div class="eyebrow">Daňový report</div><h1>Posouzení srážkové daně</h1><p>Vyhodnocení konkrétní přeshraniční platby z České republiky na základě zadaných skutkových údajů a relevantních právních pravidel.</p></div><aside class="result-card"><span>Závěr</span><strong>{escape(conclusion)}</strong><p>{escape(conclusion_detail)}</p></aside></div>
<div class="transaction-strip"><div><span>Zdroj</span><strong>{escape(str(scope.get('source_country') or '—'))}</strong></div><div><span>Příjemce</span><strong>{escape(str(scope.get('recipient_country') or '—'))}</strong></div><div><span>Příjem</span><strong>{escape(_income_type_label(scope.get('income_type')))}</strong></div><div><span>Datum</span><strong>{_report_date(scope.get('transaction_date'))}</strong></div><div><span>Částka</span><strong>{amount_copy}</strong></div></div>
<section><h2>Výpočet daně</h2>{calculation_html}</section>
<section><h2>Odůvodnění výsledku</h2><div class="summary-box"><p>{why_result}</p></div></section>
<section><h2>Podmínky a doporučené podklady</h2><div class="two-col"><div><h3>Otevřené skutkové údaje</h3><ul>{missing_items}</ul></div><div><h3>Dokumentace k transakci</h3><ul>{documents}</ul></div></div></section>
<section><h2>Daňový kalendář</h2><div class="deadlines">{compliance_html}</div></section>
<section><h2>Právní základ</h2>{''.join(source_items)}</section>
</main><footer>{escape(str(report['disclaimer']))}</footer></article></body></html>'''
'''
    p.write_text(prefix + renderer, encoding="utf-8")


def patch_tests() -> None:
    for rel in ["tests/test_workspace_report_export.py", "scripts/check_workspace_report_export.py", "scripts/render_professional_report_acceptance.py"]:
        p = ROOT / rel
        t = p.read_text(encoding="utf-8")
        t = t.replace("Otevřít profesionální report", "Tisk / PDF reportu")
        t = t.replace("Otevřít report", "Tisk / PDF")
        t = t.replace("Otevřít výstup", "Tisk / PDF")
        t = t.replace("workspace-report-export.js?v=20260817-1", "workspace-report-export.js?v=20260817-2")
        t = t.replace("workspace-output-history.css?v=20260817-1", "workspace-output-history.css?v=20260817-2")
        p.write_text(t, encoding="utf-8")


def main() -> None:
    patch_html(); patch_design_css(); patch_export_js(); patch_reporting(); patch_tests()
    print("Unified forest redesign applied")

if __name__ == "__main__": main()
