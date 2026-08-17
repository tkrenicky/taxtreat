from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_all(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def patch_workspace_html() -> None:
    p = ROOT / "app/web/workspace.html"
    replace_all(p, [
        ("Kontroly plateb", "Výpočty"),
        ("Nová kontrola platby →", "Nový výpočet →"),
        ("proveď první kontrolu platby", "proveď první výpočet podle zadaných údajů"),
        ("První platba vyhodnocena", "První výpočet dokončen"),
        ("Otevřené kontroly", "Rozpracované výpočty"),
        ("bez rozpracované platby", "bez rozpracovaného výpočtu"),
        ("Po dokončení kontroly platby se zde objeví její výsledek.", "Po dokončení výpočtu se zde zobrazí informační výstup podle zadaných údajů."),
        ("Kontrola platby", "Výpočet podle zadaných údajů"),
        ("Výsledek", "Informace podle zadaných údajů"),
        ("Podmínky a další kroky", "Podmínky použitého pravidla"),
        ("Důvod", "Použité právní pravidlo"),
    ])
    text = p.read_text(encoding="utf-8")
    marker = '<div class="demo-notice" role="status">'
    if marker in text and "TaxTreat neposkytuje daňové poradenství" not in text:
        text = text.replace(
            marker,
            marker + '\n    <span class="information-only-note"><strong>Informační nástroj:</strong> TaxTreat zobrazuje automatizované informace z právních zdrojů a zadaných údajů; neposkytuje individuální daňové nebo právní poradenství ani doporučení.</span>',
            1,
        )
    p.write_text(text, encoding="utf-8")


def patch_workspace_js() -> None:
    p = ROOT / "app/web/workspace.js"
    text = p.read_text(encoding="utf-8")
    replacements = [
        ("Vyhodnotit vstupní údaje →", "Zobrazit pravidla a výpočet →"),
        ("Doplnit údaje a dokončit kontrolu →", "Doplnit údaje a aktualizovat výpočet →"),
        ("VÝSLEDEK DOKONČEN", "VÝPOČET DOKONČEN"),
        ("ODBORNÉ OVĚŘENÍ", "CHYBÍ ÚDAJE PRO PŘIŘAZENÍ PRAVIDLA"),
        ("Bez otevřených odborných položek", "Všechny údaje potřebné pro přiřazení pravidla jsou zadány"),
        ("Zadané údaje postačují pro dokončení výpočtu.", "TaxTreat může z uvedených údajů zobrazit odpovídající pravidlo a mechanický výpočet."),
        ("Pro tento výsledek nebyl vrácen konkrétní odkaz na právní zdroj.", "Pro tento informační výstup nebyl vrácen konkrétní odkaz na právní zdroj."),
        ("Po dokončení posouzení", "Po doplnění údajů"),
        ("dokud není určeno konečné daňové zacházení", "dokud zadané údaje neumožní přiřadit příslušné pravidlo"),
        ("Výpočet se nepodařilo dokončit.", "Informační výpočet se nepodařilo dokončit."),
        ("Po vyhodnocení bude možné zadat kurz ručně", "Po doplnění údajů bude možné zadat kurz ručně"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    anchor = '''  function renderResult(payload, response) {\n'''
    helper = '''  function informationalRuleStatement(analysis) {\n    const selected = selectedRuleId(analysis);\n    const citation = [...(analysis.legal_path || analysis.citations || [])]\n      .find((item) => String(item.rule_id || "") === selected);\n    let reference = "použitého právního pravidla";\n    if (citation) {\n      const paragraph = citation.paragraph ? `, ${citation.paragraph}` : "";\n      reference = ["treaty", "protocol", "mli"].includes(String(citation.legal_layer || ""))\n        ? `článku ${citation.article || "—"}${paragraph} smlouvy o zamezení dvojího zdanění`\n        : `§ ${citation.article || "—"}${paragraph} zákona č. 586/1992 Sb., o daních z příjmů`;\n    }\n    const treatment = analysis.tax_treatment || analysis.candidate_tax_treatment;\n    if (treatment === "exclusive_foreign_taxation") {\n      return `Podle ${reference} je v TaxTreat při zadaných údajích přiřazeno pravidlo, podle něhož se příjem v České republice nezdaňuje.`;\n    }\n    if (treatment === "domestic_exemption") {\n      return `Podle ${reference} je v TaxTreat při zadaných údajích přiřazeno pravidlo osvobození.`;\n    }\n    const rate = analysis.rate ?? analysis.candidate_rate;\n    if (rate !== null && rate !== undefined) {\n      return `Podle ${reference} je v TaxTreat při zadaných údajích přiřazena sazba ${new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 2 }).format(Number(rate))} %.`;\n    }\n    return `Zadané údaje zatím neumožňují v TaxTreat přiřadit konkrétní právní pravidlo a sazbu.`;\n  }\n\n'''
    if helper not in text:
        text = text.replace(anchor, helper + anchor, 1)
    text = text.replace('setText("#workspace-reason", resultExplanation(analysis, payload));', 'setText("#workspace-reason", informationalRuleStatement(analysis));')
    text = text.replace('`Identifikovaná sazba: ${analysis.candidate_rate} %`', '`Sazba přiřazená podle dostupných údajů: ${analysis.candidate_rate} %`')
    p.write_text(text, encoding="utf-8")


def patch_export_js() -> None:
    p = ROOT / "app/web/workspace-report-export.js"
    replace_all(p, [
        ("Po dokončení kontroly platby se zde objeví její výsledek.", "Po dokončení výpočtu se zde zobrazí informační výstup podle zadaných údajů."),
        ("Výstup vznikne po dokončení kontroly platby.", "Výstup vznikne po dokončení informačního výpočtu."),
        ("Zatím bez kontrol plateb", "Zatím bez výpočtů"),
        ("Dokončené kontroly", "Dokončené výpočty"),
        ("výsledků s otevřenými podmínkami", "výpočtů s chybějícími údaji"),
        ("Nejprve dokonči výpočet. Report lze vytvořit až z vyhodnocené platby.", "Nejprve dokonči výpočet podle zadaných údajů. PDF lze vytvořit až po přiřazení právních pravidel."),
    ])


def patch_reporting() -> None:
    p = ROOT / "taxtreat/services/reporting.py"
    text = p.read_text(encoding="utf-8")
    old_disclaimer = '''DISCLAIMER = (\n    "Výstup vychází ze zadaných údajů a z právních pravidel evidovaných "\n    "v TaxTreat. Slouží jako pracovní podklad a nepředstavuje právní ani "\n    "daňové poradenství nebo závazné stanovisko správce daně."\n)'''
    new_disclaimer = '''DISCLAIMER = (\n    "TaxTreat je informační nástroj. Automatizovaně zobrazuje informace "\n    "odvozené z uvedených právních zdrojů a z údajů zadaných uživatelem. "\n    "Neprovádí individuální právní ani daňové posouzení, neposkytuje "\n    "doporučení ani právní či daňové poradenství a neurčuje postup uživatele. "\n    "Uživatel odpovídá za správnost vstupních údajů a za vlastní posouzení "\n    "použitelnosti zobrazených informací."\n)'''
    text = text.replace(old_disclaimer, new_disclaimer)

    start = text.index('def _result_copy(result: Mapping[str, Any]) -> tuple[str, str]:')
    end = text.index('\n\ndef _source_title', start)
    new_result_copy = '''def _result_copy(result: Mapping[str, Any], source_title: str | None = None) -> tuple[str, str]:\n    reference = source_title or "použité právní pravidlo"\n    treatment = result.get("tax_treatment")\n    if treatment == "exclusive_foreign_taxation":\n        return (\n            f"Podle {reference} je při zadaných údajích přiřazeno pravidlo bez českého zdanění",\n            "TaxTreat automatizovaně přiřadil právní pravidlo k údajům zadaným uživatelem; nejde o individuální daňové posouzení.",\n        )\n    if treatment == "domestic_exemption":\n        return (\n            f"Podle {reference} je při zadaných údajích přiřazeno pravidlo osvobození",\n            "TaxTreat automatizovaně přiřadil právní pravidlo k údajům zadaným uživatelem; nejde o individuální daňové posouzení.",\n        )\n    if result.get("status") == "FINAL" and result.get("rate") is not None:\n        return (\n            f"Podle {reference} je při zadaných údajích přiřazena sazba {_format_rate(result['rate'])}",\n            "Sazba je zobrazena jako automatizované přiřazení pravidla k zadaným údajům, nikoli jako daňové doporučení nebo stanovisko.",\n        )\n    return (\n        "Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo",\n        "Po doplnění otevřených údajů TaxTreat znovu zobrazí pravidla odpovídající zadaným skutečnostem.",\n    )'''
    text = text[:start] + new_result_copy + text[end:]

    text = text.replace('    conclusion, conclusion_detail = _result_copy(result)\n', '')
    selected_anchor = '''    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")\n    selected_source = next(\n        (source for source in report.get("official_sources", []) if source.get("rule_id") == selected_rule_id),\n        None,\n    )\n'''
    selected_replacement = selected_anchor + '''    selected_source_title = _source_title(selected_source) if selected_source else None\n    conclusion, conclusion_detail = _result_copy(result, selected_source_title)\n'''
    text = text.replace(selected_anchor, selected_replacement, 1)

    replacements = [
        ("Vyhodnocení konkrétní přeshraniční platby z České republiky na základě zadaných skutkových údajů a relevantních právních pravidel.", "Automatizovaný přehled právních pravidel a mechanického výpočtu vztahujícího se k údajům zadaným uživatelem."),
        ("<div class=\"eyebrow\">Daňový report</div><h1>Posouzení srážkové daně</h1>", "<div class=\"eyebrow\">Informační výstup</div><h1>Informace k české srážkové dani</h1>"),
        ("<span>Závěr</span>", "<span>Pravidlo přiřazené k zadaným údajům</span>"),
        ("<section><h2>Odůvodnění výsledku</h2>", "<section><h2>Použité právní pravidlo</h2>"),
        ("<section><h2>Podmínky a doporučené podklady</h2>", "<section><h2>Zadané podmínky a související podklady</h2>"),
        ("<h3>Dokumentace k transakci</h3>", "<h3>Související podklady</h3>"),
        ("Výsledek vychází ze zadaných údajů a z právních pravidel uvedených v tomto výstupu.", "TaxTreat přiřadil právní pravidlo k údajům zadaným uživatelem."),
        ("Před použitím výsledku je potřeba doplnit otevřené skutkové údaje nebo uzavřít označené podmínky.", "Zadané údaje zatím neumožňují přiřadit konkrétní právní pravidlo."),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    paths = [
        ROOT / "tests/test_workspace_report_export.py",
        ROOT / "scripts/check_workspace_report_export.py",
        ROOT / "scripts/render_professional_report_acceptance.py",
    ]
    for p in paths:
        text = p.read_text(encoding="utf-8")
        text = text.replace("Posouzení srážkové daně", "Informace k české srážkové dani")
        text = text.replace("Odůvodnění výsledku", "Použité právní pravidlo")
        text = text.replace("Dokončené kontroly", "Dokončené výpočty")
        text = text.replace("výsledků s otevřenými podmínkami", "výpočtů s chybějícími údaji")
        p.write_text(text, encoding="utf-8")


def main() -> None:
    patch_workspace_html()
    patch_workspace_js()
    patch_export_js()
    patch_reporting()
    patch_tests()
    print("Information-only wording applied")


if __name__ == "__main__":
    main()
