from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch(ROOT / "app/web/index.html", [
        ("mechanický výpočet", "výpočet podle zadaných údajů"),
        ("mechanického výpočtu", "výpočtu podle zadaných údajů"),
    ])
    patch(ROOT / "app/web/app.js", [
        ("provedl mechanický výpočet", "provedl výpočet podle zadaných údajů"),
    ])
    patch(ROOT / "app/web/workspace.js", [
        ("odpovídající pravidlo a mechanický výpočet", "odpovídající pravidlo a výpočet podle zadaných údajů"),
    ])

    report = ROOT / "taxtreat/services/reporting.py"
    text = report.read_text(encoding="utf-8")
    text = text.replace("mechanického výpočtu", "výpočtu podle zadaných údajů")
    text = text.replace("mechanický výpočet", "výpočet podle zadaných údajů")
    text = text.replace("<small>Analýza české srážkové daně</small>", "<small>Informace k české srážkové dani</small>")
    text = text.replace("Částka zadaná pro analyzovanou transakci", "Částka zadaná pro tuto transakci")
    text = text.replace(
        '    selected_source = next((s for s in report.get("official_sources", []) if s.get("rule_id") == selected_rule_id), None)\n',
        '    selected_source = next((s for s in report.get("official_sources", []) if s.get("rule_id") == selected_rule_id), None)\n    selected_source_title = _source_title(selected_source) if selected_source else None\n    conclusion, conclusion_detail = _result_copy(result, selected_source_title)\n',
        1,
    )
    text = text.replace(
        '        why_result = f"Sazba vychází z {_source_title(selected_source)} a ze skutkových údajů potvrzených pro tuto transakci."',
        '        why_result = f"Podle {_source_title(selected_source)} je v TaxTreat při zadaných údajích přiřazeno pravidlo použité ve výpočtu."',
    )
    text = text.replace(
        '        why_result = f"Výsledek vychází z {_source_title(selected_source)} a ze skutkových údajů potvrzených pro tuto transakci."',
        '        why_result = f"Podle {_source_title(selected_source)} je v TaxTreat při zadaných údajích přiřazeno pravidlo použité ve výpočtu."',
    )
    text = text.replace(
        '        why_result = "Výsledek vychází ze zadaných údajů a z právních podkladů uvedených v tomto reportu."',
        '        why_result = "TaxTreat zobrazuje pravidla přiřazená k zadaným údajům a právní zdroje uvedené v tomto výstupu."',
    )
    report.write_text(text, encoding="utf-8")

    positioning = ROOT / "tests/test_information_only_positioning.py"
    text = positioning.read_text(encoding="utf-8")
    text = text.replace(
        '    "Otevřít profesionální report",\n)',
        '    "Otevřít profesionální report",\n    "mechanický výpočet",\n    "mechanického výpočtu",\n)',
    )
    positioning.write_text(text, encoding="utf-8")

    for rel in ["scripts/check_workspace_report_export.py", "scripts/render_professional_report_acceptance.py"]:
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        text = text.replace("mechanický výpočet", "výpočet podle zadaných údajů")
        text = text.replace("mechanického výpočtu", "výpočtu podle zadaných údajů")
        p.write_text(text, encoding="utf-8")

    print("Information report fixed; mechanical wording removed")


if __name__ == "__main__":
    main()
