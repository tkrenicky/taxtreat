from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    path = ROOT / "app" / "web" / "workspace.js"
    text = path.read_text(encoding="utf-8")
    old = '`Zdanění pouze ve státě rezidence příjemce (${countryNames[recipient.country]})`'
    new = '`Zdanění pouze ve státě rezidence příjemce (${countryName(recipient.country)})`'
    if old not in text:
        raise RuntimeError("Legacy countryNames runtime reference not found")
    text = text.replace(old, new, 1)
    text = text.replace(
        '"Sazbu nelze určit bez odborného posouzení"',
        '"Sazbu nelze určit bez doplnění potřebných podmínek"',
    )
    if "countryNames" in text:
        raise RuntimeError("Legacy countryNames reference remains in workspace.js")
    path.write_text(text, encoding="utf-8")

    test = ROOT / "tests" / "test_stage7b_ui.py"
    source = test.read_text(encoding="utf-8")
    marker = '    assert "routeDesign" in javascript.text\n'
    insertion = marker + '    assert "countryNames" not in javascript.text\n    assert "countryName(recipient.country)" in javascript.text\n'
    if marker not in source:
        raise RuntimeError("UI test insertion marker missing")
    test.write_text(source.replace(marker, insertion, 1), encoding="utf-8")
    print("Country-name runtime reference fixed")


if __name__ == "__main__":
    main()
