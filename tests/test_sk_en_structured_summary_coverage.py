from __future__ import annotations

import json
from pathlib import Path

from taxtreat.services.report_locales import english_excerpt_for_citation


ROOT = Path(__file__).resolve().parents[1]
PARTNERS = ROOT / "data" / "sk_treaty_partners.json"
RULES = ROOT / "data" / "legal_rules_sk"
INCOMES = {"dividend", "interest", "royalty"}
LEGAL_LAYERS = {"treaty", "protocol", "mli"}


def test_sk_english_structured_summary_covers_all_partner_income_scopes():
    partners = json.loads(PARTNERS.read_text(encoding="utf-8"))
    assert len(partners) == 75

    covered_scopes = set()
    checked_rules = 0
    review_required = 0
    verified = 0

    for partner in partners:
        country = str(partner["iso2"]).upper()
        path = RULES / f"{country.lower()}.json"
        assert path.is_file(), country
        payload = json.loads(path.read_text(encoding="utf-8"))

        for rule in payload.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            if str(rule.get("legal_layer") or "") not in LEGAL_LAYERS:
                continue
            if str(rule.get("verification_status") or "") not in {"verified", "needs_review"}:
                continue

            rule_id = str(rule.get("rule_id") or "")
            assert rule_id
            summary = english_excerpt_for_citation(
                {
                    "rule_id": rule_id,
                    "article": rule.get("article"),
                    "legal_layer": rule.get("legal_layer"),
                },
                country,
                "SK",
            )
            assert summary is not None, rule_id
            assert summary["excerpt_language"] == "en"
            assert "not treaty wording" in summary["excerpt_status_label"].lower()
            assert "Czech source-state" not in summary["excerpt"]
            assert "Czech treaty" not in summary["excerpt"]
            assert summary["excerpt_source_url"] == rule.get("source_url")
            checked_rules += 1

            if summary["excerpt_status"] == "review_required_structured_rule_summary":
                review_required += 1
                assert "no final" in summary["excerpt"].lower() or "review-required" in summary["excerpt"].lower()
            else:
                verified += 1
                assert summary["excerpt_status"] == "verified_structured_rule_summary"

            income = str(rule.get("income_type") or "")
            if income in INCOMES:
                covered_scopes.add((country, income))

    expected_scopes = {
        (str(partner["iso2"]).upper(), income)
        for partner in partners
        for income in INCOMES
    }
    assert covered_scopes == expected_scopes
    assert len(covered_scopes) == 225
    assert checked_rules > 225
    assert review_required > 0
    assert verified > 0

    print(
        "SK EN structured summary coverage: "
        f"75/75 partners; 225/225 income scopes; "
        f"{checked_rules} treaty/protocol/MLI rules; "
        f"{verified} verified summaries; {review_required} review-required summaries"
    )


def test_sk_english_summary_fails_closed_for_unknown_or_cross_pair_rule():
    assert english_excerpt_for_citation(
        {"rule_id": "SK-AT-NOT-A-RULE", "article": "10"}, "AT", "SK"
    ) is None
    assert english_excerpt_for_citation(
        {"rule_id": "SK-AT-INTEREST-TREATY-INTEREST-RESIDENCE-ONLY", "article": "11"},
        "DE",
        "SK",
    ) is None
