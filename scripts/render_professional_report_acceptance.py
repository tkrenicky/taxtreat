from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

from app.main import app
from taxtreat.services.legal_sources import load_verified_provisions


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "professional_report_acceptance"


def _payload() -> dict:
    return {
        "source_country": "CZ",
        "recipient_country": "AD",
        "income_type": "dividend",
        "transaction_date": "2026-08-16",
        "facts": {
            "recipient_tax_residence": "confirmed",
            "recipient_legal_form": "company",
            "beneficial_owner": True,
            "beneficial_owner_confirmed": True,
            "anti_abuse_review_passed": True,
            "residence_certificate_available": True,
            "no_pe_connection": True,
            "pe_connection": False,
            "ownership_percent": 100,
            "direct_ownership": True,
            "holding_period_months": 24,
            "recipient_is_qualifying_company": True,
        },
        "determinations": {},
        "transaction_amount": {
            "amount": "100000",
            "currency": "CZK",
            "payment_date": "2026-08-16",
            "accounting_date": "2026-08-16",
        },
    }


def render(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    response = client.post("/analysis/report", json=_payload())
    response.raise_for_status()
    payload = response.json()
    report = payload["report"]
    html = payload["html"]

    canonical = load_verified_provisions()["CZ-AD|treaty|10"]
    canonical_text = canonical["text"]
    canonical_heading = canonical_text.splitlines()[0].strip()
    if canonical_text not in html:
        raise AssertionError("Canonical AD Article 10 text is absent from report HTML.")
    for damaged in ("rozdili zisk", "vyplacejici"):
        if damaged in html:
            raise AssertionError(f"Damaged Stage 6 wording leaked into report HTML: {damaged}")

    html_path = output_dir / "taxtreat-professional-report.html"
    pdf_path = output_dir / "taxtreat-professional-report.pdf"
    png_path = output_dir / "taxtreat-professional-report.png"
    metadata_path = output_dir / "acceptance.json"
    html_path.write_text(html, encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1600})
        page.set_content(html, wait_until="load")

        # Legal provisions are collapsible in the interactive HTML report. A
        # PDF is an archival output, so every cited provision must be expanded
        # before Chromium prints the document.
        page.locator("details").evaluate_all(
            "nodes => nodes.forEach(node => { node.open = true; })"
        )

        body_text = page.locator("body").inner_text()
        if "Česká srážková daň" not in body_text:
            raise AssertionError("Rendered report is missing its main heading.")
        if "Použité právní podklady" not in body_text:
            raise AssertionError("Rendered report is missing legal-source section.")
        if canonical_heading not in body_text:
            raise AssertionError("Expanded report does not contain the canonical article heading.")

        page.emulate_media(media="print")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
        )
        page.emulate_media(media="screen")
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()

    pdf_bytes = pdf_path.read_bytes()
    if not pdf_bytes.startswith(b"%PDF-"):
        raise AssertionError("Chromium output is not a valid PDF.")
    if len(pdf_bytes) < 20_000:
        raise AssertionError("Rendered PDF is unexpectedly small.")

    pdf_text = "\n".join(
        page.extract_text() or ""
        for page in PdfReader(str(pdf_path)).pages
    )
    if canonical_heading not in pdf_text:
        raise AssertionError("Printed PDF does not contain the canonical article heading.")
    for damaged in ("rozdili zisk", "vyplacejici"):
        if damaged in pdf_text:
            raise AssertionError(f"Damaged Stage 6 wording leaked into PDF: {damaged}")

    result = {
        "schema_version": 1,
        "report_id": report["report_id"],
        "html_bytes": html_path.stat().st_size,
        "pdf_bytes": len(pdf_bytes),
        "screenshot_bytes": png_path.stat().st_size,
        "canonical_source_key": "CZ-AD|treaty|10",
        "canonical_text_sha256": canonical["verified_text_sha256"],
        "official_pdf_sha256": canonical["official_pdf_sha256"],
        "damaged_stage6_wording_absent": True,
        "html_rendered": True,
        "pdf_rendered": True,
        "pdf_contains_canonical_heading": True,
        "pass": True,
    }
    metadata_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    result = render(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
