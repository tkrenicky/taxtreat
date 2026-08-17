from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from taxtreat.services.reporting import render_report_html


_DOMESTIC_LOCATOR = "§ 36 odst. 1 písm. b) bod 1"
_INTERNAL_DOMESTIC_LOCATOR = "§ 36 odst. odst. 1"


def _sample_report() -> dict:
    return {
        "report_id": "TAXTREAT-ACCEPTANCE",
        "generated_at": "2026-08-17T10:00:00Z",
        "legal_data_cutoff": "2026-08-12",
        "legal_dataset_release": "acceptance-release",
        "source_release": "acceptance-source",
        "scope": {
            "source_country": "CZ",
            "recipient_country": "AD",
            "income_type": "dividend",
            "transaction_date": "2026-08-17",
            "transaction_amount": {"amount": 1000000, "currency": "CZK"},
        },
        "assumptions": {
            "transaction_facts": {
                "beneficial_owner": True,
                "recipient_is_treaty_resident": True,
                "permanent_establishment_connection": False,
                "ownership_percent": 100,
                "direct_ownership": True,
                "holding_period_months": 24,
            },
            "user_determinations": {},
        },
        "result": {
            "status": "FINAL",
            "rate": 5,
            "tax_treatment": "treaty_rate",
            "selected_rule_id": "CZ-AD-DIV-5",
            "candidate_rule_id": None,
            "withholding_tax_calculation": {
                "status": "CALCULATED",
                "gross_amount_czk": 1000000,
                "withholding_tax_czk": 50000,
                "net_amount_czk": 950000,
            },
            "withholding_compliance_schedule": {
                "remittance_deadline": "2026-09-30",
                "notification_deadline": "2026-09-30",
            },
        },
        "official_sources": [
            {
                "rule_id": "CZ-DOM-DIV",
                "source_id": "CZ-ZDP",
                "source_url": "https://www.zakonyprolidi.cz/cs/1992-586",
                "article": "36",
                "paragraph": "1 písm. b) bod 1",
                "legal_layer": "domestic",
                "legal_instrument": "ZDP",
                "rate": 15,
                "excerpt": "§ 36",
            },
            {
                "rule_id": "CZ-AD-DIV-5",
                "source_id": "CZ-AD-DTT",
                "source_url": "https://www.e-sbirka.cz/",
                "article": "10",
                "paragraph": "2",
                "legal_layer": "treaty",
                "legal_instrument": "CZ-AD DTT",
                "rate": 5,
                "excerpt": (
                    "Článek 10\nDIVIDENDY\n"
                    "1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě.\n"
                    "2. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, však mohou být rovněž zdaněny v tomto státě, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne:\n"
                    "a) 5 procent hrubé částky dividend, jestliže skutečným vlastníkem je společnost (jiná než osobní společnost), která přímo drží alespoň 10 procent kapitálu společnosti vyplácející dividendy;\n"
                    "b) 10 procent hrubé částky dividend ve všech ostatních případech.\n"
                    "Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny.\n"
                    "3. Výraz dividendy se použije v tomto článku.\n"
                    "4. Další ustanovení."
                ),
            },
        ],
        "missing_facts": [],
        "required_documentation": [],
        "explanation": [],
        "disclaimer": "TaxTreat je informační nástroj. Automatizovaně zobrazuje informace z právních zdrojů.",
    }


def render(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "taxtreat-professional-report.html"
    pdf_path = output_dir / "taxtreat-professional-report.pdf"
    png_path = output_dir / "taxtreat-professional-report.png"

    html = render_report_html(_sample_report())
    html_path.write_text(html, encoding="utf-8")

    canonical_heading = "Smlouva mezi Českou republikou a Andorrou o zamezení dvojího zdanění, čl. 10 (Dividendy)"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")

        body_text = page.locator("body").inner_text()
        if "Informace k české srážkové dani" not in body_text:
            raise AssertionError("Rendered report is missing its main heading.")
        legal_basis = page.locator(
            ".legal-basis-kicker",
            has_text="Právní základ",
        )
        if legal_basis.count() != 1:
            raise AssertionError("Rendered report is missing its legal-basis section.")
        if canonical_heading not in body_text:
            raise AssertionError("Expanded report does not contain the canonical article heading.")
        legal_cards = page.locator(".legal-source")
        if legal_cards.count() != 1:
            raise AssertionError("Rendered report must contain exactly one primary legal-source card.")
        legal_card_text = legal_cards.first.inner_text()
        if "čl. 10" not in legal_card_text or "Andorrou" not in legal_card_text:
            raise AssertionError("Primary legal-source card does not identify the treaty and Article 10.")
        if _DOMESTIC_LOCATOR not in body_text or _INTERNAL_DOMESTIC_LOCATOR in body_text:
            raise AssertionError("Rendered report uses an invalid domestic legal locator format.")

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

    result = {
        "html": str(html_path),
        "pdf": str(pdf_path),
        "png": str(png_path),
    }
    (output_dir / "acceptance.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/professional_report_acceptance"),
    )
    args = parser.parse_args()
    result = render(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
