from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> int:
    loader = (WEB / "workspace-report-export.js").read_text(encoding="utf-8")
    intake_en = (WEB / "workspace-dynamic-intake-en-20260830.js").read_text(encoding="utf-8")
    report_context = (WEB / "workspace-report-context.js").read_text(encoding="utf-8")
    status_integrity = (WEB / "workspace-output-status-integrity-20260830.js").read_text(encoding="utf-8")
    locale_engine = (ROOT / "taxtreat" / "services" / "web_locale_engine.py").read_text(encoding="utf-8")
    main_py = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

    require(
        loader,
        "/ui-assets/workspace-dynamic-intake-en-20260830.js?v=20260830-intake1",
        "workspace loader",
    )
    require(
        loader,
        "/ui-assets/workspace-output-status-integrity-20260830.js?v=20260830-status1",
        "workspace loader",
    )

    # Dynamic treaty questions must be localized from the structured response,
    # keyed by the condition fact, rather than by rewriting already-rendered DOM.
    require(intake_en, "url.includes(\"/analysis/intake\")", "EN dynamic intake")
    require(intake_en, "localizeIntake", "EN dynamic intake")
    require(intake_en, "question?.input_path", "EN dynamic intake")
    require(intake_en, "response.clone().json()", "EN dynamic intake")
    require(intake_en, "new Response(JSON.stringify(body)", "EN dynamic intake")
    require(intake_en, "article_10_public_body_exemption", "EN dynamic intake")
    require(intake_en, "article_11_public_body_exemption", "EN dynamic intake")
    require(intake_en, "recipient_is_bank", "EN dynamic intake")
    if "MutationObserver" in intake_en or "#workspace-questions" in intake_en:
        raise AssertionError("EN dynamic intake regressed to DOM text translation")

    # /ui/en is a locale-owned runtime. Report language must therefore fall
    # back to the route locale/localStorage even when no legacy language select exists.
    require(report_context, "window.__TAXTREAT_LOCALE__", "report language context")
    require(report_context, 'localStorage.getItem("taxtreat-report-language")', "report language context")
    require(report_context, "payload.facts.__report_language", "report language context")
    require(main_py, 'facts.pop("__report_language"', "report endpoint")
    require(main_py, "language=report_language", "report endpoint")
    require(locale_engine, 'localStorage.setItem("taxtreat-report-language", "en")', "locale router")

    # REVIEW outputs may stay in history but must not be counted as completed.
    require(status_integrity, ".review-history-status.attention", "output status integrity")
    require(status_integrity, "completedCount = Math.max(0, rows.length - reviewCount)", "output status integrity")
    require(status_integrity, "FINAL results in this browser session", "output status integrity")

    print("Web/report condition-aware integration regressions: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
