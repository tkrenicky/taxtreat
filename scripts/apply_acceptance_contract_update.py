from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Missing expected contract in {path}: {old}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    browser = ROOT / "scripts" / "check_workspace_report_export.py"
    replace_required(browser, 'report_page.locator(".source").count()', 'report_page.locator(".legal-source").count()')

    report = ROOT / "scripts" / "render_professional_report_acceptance.py"
    replace_required(report, '"Použité právní podklady"', '"Právní základ"')

    static = ROOT / "tests" / "test_workspace_report_export.py"
    replace_required(static, "/ui-assets/workspace-report-export.js?v=20260816-1", "/ui-assets/workspace-report-export.js?v=20260817-1")
    replace_required(static, "/ui-assets/workspace-output-history.css?v=20260816-2", "/ui-assets/workspace-output-history.css?v=20260817-1")
    replace_required(static, "výsledků k odbornému ověření", "výsledků s otevřenými podmínkami")
    print("Acceptance contracts updated.")


if __name__ == "__main__":
    main()
