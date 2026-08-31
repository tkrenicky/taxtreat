from __future__ import annotations

from taxtreat.services.report_locales import english_excerpt_for_citation
from taxtreat.services.reporting import build_professional_report


def main() -> int:
    citation = {
        "rule_id": "CZ-BG-DIVIDEND-CURRENT-1",
        "article": "10",
        "legal_layer": "treaty",
        "source_url": "https://e-sbirka.gov.cz/sb/1999/203/0000-00-00",
        "rate": 10,
        "tax_treatment": "source_tax_limited",
        "path_role": "applied_treaty_rule",
    }
    locale = english_excerpt_for_citation(citation, "BG")
    assert locale
    assert locale["excerpt_language"] == "en"
    assert locale["excerpt_status"] == "verified_stage6_rule_summary"
    assert "maximum Czech source-state withholding rate of 10%" in locale["excerpt"]

    analysis = {
        "status": "FINAL",
        "rate": 10,
        "tax_treatment": "source_tax_limited",
        "selected_rule_id": "CZ-BG-DIVIDEND-CURRENT-1",
        "legal_path": [citation],
        "citations": [citation],
        "layer_results": [],
        "explanation": [],
    }
    request = {
        "source_country": "CZ",
        "recipient_country": "BG",
        "income_type": "dividend",
        "transaction_date": "2026-08-11",
        "transaction_amount": 100000,
        "facts": {},
        "determinations": {},
    }
    report = build_professional_report(request, analysis, language="en")
    source = report["official_sources"][0]
    assert source["excerpt_language"] == "en"
    assert source["excerpt_status"] == "verified_stage6_rule_summary"
    assert "Verified English rule summary" in source["excerpt_status_label"]
    assert "maximum Czech source-state withholding rate of 10%" in source["excerpt"]
    print("EN fallback report locale acceptance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
