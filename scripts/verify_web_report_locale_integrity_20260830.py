from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def require(path: Path, needle: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        raise AssertionError(f"Missing {label}: {needle}")


def main() -> int:
    loader = WEB / "workspace-report-export.js"
    dynamic_intake = WEB / "workspace-dynamic-intake-en-20260830.js"
    report_context = WEB / "workspace-report-context.js"
    output_integrity = WEB / "workspace-output-status-integrity-20260830.js"

    require(loader, "workspace-dynamic-intake-en-20260830.js", "dynamic EN intake asset in loader")
    require(loader, "workspace-output-status-integrity-20260830.js", "output status integrity asset in loader")

    require(dynamic_intake, 'url.includes("/analysis/intake")', "structured intake interception")
    require(dynamic_intake, "question?.input_path", "fact-aware intake localization")
    require(dynamic_intake, "body?.intake?.questions", "structured question localization")
    require(dynamic_intake, "response.clone().json()", "response-level localization")
    if "MutationObserver" in dynamic_intake or "question-card" in dynamic_intake:
        raise AssertionError("Dynamic EN intake must localize structured response data, not patch rendered DOM")

    require(report_context, "window.__TAXTREAT_LOCALE__", "report locale route fallback")
    require(report_context, 'localStorage.getItem("taxtreat-report-language")', "stored report locale fallback")
    require(report_context, "payload.facts.__report_language = reportLanguage();", "report language payload propagation")

    require(output_integrity, 'record.status === "FINAL"', "FINAL-only completed metric")
    require(output_integrity, "statusNeedsReview(record.status)", "separate review metric")

    print("Web/report locale and status integrity: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
